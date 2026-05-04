# main.py
# Face Recognition Home Security System

from fileinput import filename

import cv2
import face_recognition
import os
import time
import threading
import numpy as np
import serial
import pyttsx3
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
import gspread
from google.oauth2.service_account import Credentials
import base64

# ─── CONFIG ──────────────────────────────────────────────
PORT            = "COM11"
BAUD            = 9600
KNOWN_FACES_DIR = "known_faces"
TOLERANCE       = 0.5
LED_ON_DURATION = 3
FRAME_SCALE     = 0.25
LOG_COOLDOWN    = 60
BURST_THRESHOLD = 3
GOOGLE_CREDS    = "credentials.json"
SHEET_NAME      = "Doorbell Log"
ADMIN_PASSWORD  = "admin123"
RELOAD_TRIGGER  = ".reload_faces"
UNKNOWN_FACES_DIR = "unknown_faces"
os.makedirs(UNKNOWN_FACES_DIR, exist_ok=True)
# ─────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)

state_lock = threading.Lock()
state = {
    "status":      "Initializing...",
    "last_person": None,
    "last_time":   None,
    "led":         False,
    "logs":        [],
    "frame_b64":   None,
}

tts_engine = pyttsx3.init()
tts_engine.setProperty("rate", 160)
tts_lock = threading.Lock()

def speak(text):
    def _speak():
        with tts_lock:
            tts_engine.say(text)
            tts_engine.runAndWait()
    threading.Thread(target=_speak, daemon=True).start()

# ── Google Sheets ─────────────────────────────────────────
sheet = None

def init_sheet():
    global sheet
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets",
                  "https://www.googleapis.com/auth/drive"]
        creds  = Credentials.from_service_account_file(GOOGLE_CREDS, scopes=scopes)
        client = gspread.authorize(creds)
        sh     = client.open(SHEET_NAME)
        sheet  = sh.sheet1
        if sheet.row_count == 0 or sheet.cell(1, 1).value != "Timestamp":
            sheet.clear()
            sheet.append_row(["Timestamp", "Person", "Type", "Status", "Image"])
        print("[INFO] Google Sheets connected.")
    except Exception as e:
        print(f"[WARNING] Google Sheets unavailable: {e}")
        sheet = None

def log_to_sheet(name, person_type):
    if sheet is None:
        return
    def _log():
        try:
            ts     = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "Access Granted" if person_type == "known" else "Access Denied"
            sheet.append_row([ts, name, person_type.capitalize(), status, filename])
        except Exception as e:
            print(f"[WARNING] Sheet log failed: {e}")
    threading.Thread(target=_log, daemon=True).start()

# ── Arduino ───────────────────────────────────────────────
ser = None

def init_serial():
    global ser
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1)
        time.sleep(2)
        led_off()
        print(f"[INFO] Arduino connected on {PORT}.")
    except Exception as e:
        print(f"[WARNING] Arduino unavailable: {e}")
        ser = None

def led_on():
    if ser:
        ser.write(b'1')
    with state_lock:
        state["led"] = True

def led_off():
    if ser:
        ser.write(b'0')
    with state_lock:
        state["led"] = False

# ── Face loading ──────────────────────────────────────────
known_encodings_global = []
known_names_global     = []
faces_lock             = threading.Lock()

def load_known_faces(directory):
    encodings, names = [], []
    if not os.path.isdir(directory):
        print(f"[ERROR] '{directory}' folder not found.")
        return encodings, names

    print("[INFO] Loading known faces...")
    for filename in sorted(os.listdir(directory)):
        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        path = os.path.join(directory, filename)
        try:
            img  = cv2.imread(path)
            if img is None:
                print(f"  ✗ Could not read {filename}")
                continue
            rgb  = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            rgb  = np.ascontiguousarray(rgb)
            locs = face_recognition.face_locations(rgb, model="hog")
            encs = face_recognition.face_encodings(rgb, locs, num_jitters=1, model="small")
            if encs:
                encodings.append(encs[0])
                names.append(os.path.splitext(filename)[0].capitalize())
                print(f"  ✓ {filename}")
            else:
                print(f"  ✗ No face in {filename}")
        except Exception as e:
            print(f"  ✗ Error loading {filename}: {e}")

    print(f"[INFO] {len(names)} face(s) loaded: {names}\n")
    return encodings, names

def reload_known_faces():
    global known_encodings_global, known_names_global
    encs, names = load_known_faces(KNOWN_FACES_DIR)
    with faces_lock:
        known_encodings_global = encs
        known_names_global     = names
    print(f"[INFO] Face list reloaded — {len(names)} face(s) now known.")

def best_match(known_encodings, known_names, enc, tolerance):
    if not known_encodings:
        return None
    distances = face_recognition.face_distance(known_encodings, enc)
    idx = int(np.argmin(distances))
    return known_names[idx] if distances[idx] <= tolerance else None

# ── File watcher — reloads faces when add_face.py signals ─
def watch_for_reload():
    last_seen = None
    while True:
        try:
            if os.path.exists(RELOAD_TRIGGER):
                mtime = os.path.getmtime(RELOAD_TRIGGER)
                if mtime != last_seen:
                    last_seen = mtime
                    print("[WATCHER] Reload trigger detected — reloading faces...")
                    reload_known_faces()
                    os.remove(RELOAD_TRIGGER)
        except Exception as e:
            print(f"[WATCHER] Error: {e}")
        time.sleep(1)

# ── Detection loop ────────────────────────────────────────
def detection_loop():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Webcam not found.")
        return

    led_on_until  = 0.0
    led_currently = False
    detection_counts = {}
    last_logged      = {}

    while True:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.05)
            continue

        small     = cv2.resize(frame, (0, 0), fx=FRAME_SCALE, fy=FRAME_SCALE)
        rgb_small = np.ascontiguousarray(small[:, :, ::-1])

        locations = face_recognition.face_locations(rgb_small, model="hog")
        encodings = face_recognition.face_encodings(rgb_small, locations, num_jitters=1, model="small")

        now         = time.time()
        found_known = False

        with faces_lock:
            cur_encodings = list(known_encodings_global)
            cur_names     = list(known_names_global)

        for (top, right, bottom, left), enc in zip(locations, encodings):
            name     = best_match(cur_encodings, cur_names, enc, TOLERANCE)
            label    = name if name else "Unknown"
            is_known = name is not None

            if is_known:
                found_known  = True
                led_on_until = now + LED_ON_DURATION
                color = (0, 220, 100)
            else:
                color = (0, 60, 220)

            detection_counts[label] = detection_counts.get(label, 0) + 1
            cooldown_ok = (now - last_logged.get(label, 0)) >= LOG_COOLDOWN
            burst_ok    = detection_counts[label] >= BURST_THRESHOLD

            if burst_ok and cooldown_ok:
                detection_counts[label] = 0
                last_logged[label]      = now
                ts_str    = datetime.now().strftime("%H:%M:%S")
                log_entry = {"name": label, "time": ts_str,
                             "type": "known" if is_known else "unknown"}
                with state_lock:
                    state["logs"].insert(0, log_entry)
                    state["logs"]        = state["logs"][:50]
                    state["last_person"] = label
                    state["last_time"]   = ts_str

                log_to_sheet(label, "known" if is_known else "unknown")

                if is_known:
                    speak("Access Granted")
                    print(f"[DETECTED] ✅ {label} — logged")
                if not is_known:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"{UNKNOWN_FACES_DIR}/unknown_{timestamp}.jpg"

                    # Crop face before saving (better than full frame)
                    s = int(1 / FRAME_SCALE)
                    t, r, b, l = top*s, right*s, bottom*s, left*s
                    face_crop = frame[t:b, l:r]

                    try:
                        cv2.imwrite(filename, face_crop)
                        print(f"[SAVED] Unknown face saved: {filename}")
                    except Exception as e:
                        print(f"[ERROR] Saving unknown face failed: {e}")
                else:
                    print(f"[DETECTED] ❌ Unknown — logged")

            s = int(1 / FRAME_SCALE)
            t, r, b, l = top*s, right*s, bottom*s, left*s
            cv2.rectangle(frame, (l, t), (r, b), color, 2)
            cv2.rectangle(frame, (l, b-30), (r, b), color, cv2.FILLED)
            cv2.putText(frame, label, (l+6, b-8),
                        cv2.FONT_HERSHEY_DUPLEX, 0.6, (255,255,255), 1)

        with state_lock:
            state["status"] = ("Known" if found_known else "Unknown") if locations else "No Face"

        should_on = now < led_on_until
        if should_on and not led_currently:
            led_on();  led_currently = True
        elif not should_on and led_currently:
            led_off(); led_currently = False

        _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
        with state_lock:
            state["frame_b64"] = base64.b64encode(buf).decode("utf-8")

    cap.release()

# ── Flask routes ──────────────────────────────────────────
@app.route("/")
def index():
    with open("templates/index.html", encoding="utf-8") as f:
        return f.read()

@app.route("/api/state")
def api_state():
    with state_lock:
        return jsonify({
            "status":      state["status"],
            "last_person": state["last_person"],
            "last_time":   state["last_time"],
            "led":         state["led"],
            "logs":        state["logs"],
            "frame":       state["frame_b64"],
        })

@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    data = request.get_json(force=True)
    if data.get("password") == ADMIN_PASSWORD:
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Wrong password"}), 401

@app.route("/api/admin/faces")
def admin_faces():
    with faces_lock:
        names = list(known_names_global)
    return jsonify({"ok": True, "faces": names, "count": len(names)})

# ── Entry point ───────────────────────────────────────────
if __name__ == "__main__":
    init_serial()
    init_sheet()

    encs, names = load_known_faces(KNOWN_FACES_DIR)
    with faces_lock:
        known_encodings_global = encs
        known_names_global     = names

    threading.Thread(target=watch_for_reload, daemon=True).start()
    threading.Thread(target=detection_loop,   daemon=True).start()

    print("[INFO] Dashboard -> http://127.0.0.1:5000\n")
    app.run(host="0.0.0.0", port=5000, debug=False)
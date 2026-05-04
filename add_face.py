# add_face.py
# Run alongside main.py — saves face then signals main.py to reload instantly.
# Controls: SPACE = capture  |  R = retake  |  Q = quit

import cv2
import face_recognition
import os
import numpy as np
from datetime import datetime

KNOWN_FACES_DIR = "known_faces"
RELOAD_TRIGGER  = ".reload_faces"   # main.py watches for this file

os.makedirs(KNOWN_FACES_DIR, exist_ok=True)

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("[ERROR] Webcam not found.")
    exit()

print("\n=== Add Face Tool ===")
print("  SPACE  -> capture frame")
print("  R      -> retake")
print("  Q      -> quit\n")

captured = None

while True:
    ret, frame = cap.read()
    if not ret:
        continue

    display = frame.copy()

    if captured is None:
        cv2.putText(display, "SPACE: capture  |  Q: quit",
                    (10, 30), cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 220, 100), 1)
    else:
        cv2.putText(display, "CAPTURED -- check terminal",
                    (10, 30), cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 220, 255), 1)
        cv2.putText(display, "R: retake  |  Q: quit",
                    (10, 60), cv2.FONT_HERSHEY_DUPLEX, 0.65, (0, 220, 255), 1)

    cv2.imshow("Add Face -- SecureVision", display)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        print("[INFO] Quit.")
        break

    elif key == ord(' ') and captured is None:
        rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb  = np.ascontiguousarray(rgb)
        locs = face_recognition.face_locations(rgb, model="hog")

        if not locs:
            print("[!] No face detected -- try again.")
            continue

        captured = frame.copy()
        print(f"[OK] Face detected.")
        print("Enter name for this person: ", end="", flush=True)
        name = input().strip()

        if not name:
            print("[!] No name entered -- retaking.")
            captured = None
            continue

        safe     = "".join(c for c in name if c.isalnum() or c in " _-").strip().replace(" ", "_")
        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        savepath = os.path.join(KNOWN_FACES_DIR, f"{safe}_{ts}.jpg")
        cv2.imwrite(savepath, captured)
        print(f"[SAVED] {savepath}")

        # Write trigger file — main.py's watcher thread picks this up and reloads
        with open(RELOAD_TRIGGER, "w") as f:
            f.write(datetime.now().isoformat())
        print(f"[SIGNAL] main.py notified -- {name} is now active immediately.\n")
        print("Press SPACE to add another, or Q to quit.")
        captured = None

    elif key == ord('r'):
        captured = None
        print("[INFO] Retaking...")

cap.release()
cv2.destroyAllWindows()
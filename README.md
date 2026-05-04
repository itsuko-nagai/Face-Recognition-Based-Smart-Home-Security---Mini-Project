# SecureVision — Face Recognition Doorbell & Security System

A smart home security system that identifies individuals in real-time, logs access attempts to Google Sheets, provides a web-based monitoring dashboard, and interacts with physical hardware via Arduino.

---

## 🚀 Features

-   **Real-Time Face Recognition:** Detects and identifies faces using the HOG model for accuracy and speed.
-   **Web Dashboard:** Live status updates, access logs, and real-time frame streaming via a Flask-based web interface.
-   **Google Sheets Integration:** Automatically logs every detection (Timestamp, Name, Type, Status) to a remote spreadsheet.
-   **Hardware Interaction:** Communicates with an Arduino to trigger physical indicators (like an LED or electronic lock).
-   **Voice Feedback:** Built-in Text-to-Speech (TTS) for "Access Granted" announcements.
-   **Dynamic Face Management:** Add new faces on the fly using the `add_face.py` tool without restarting the main system.

---

## 🛠️ Hardware Requirements

1.  **Webcam:** Standard USB webcam or integrated laptop camera.
2.  **Arduino:** (Optional) Connected via Serial (default `COM4`).
    -   Indicator LED or Relay on **Digital Pin 10**.
3.  **PC:** Capable of running Python 3.x with OpenCV.

---

## 📦 Software Setup

### 1. Install Dependencies
Ensure you have Python 3.8+ installed, then run:
```bash
pip install -r req.txt
```

### 2. Arduino Configuration
-   Open `arduino_code/arduino_code.ino` in the Arduino IDE.
-   Upload the code to your board.
-   Ensure the board is connected to the port specified in `main.py` (default: `COM4`).

### 3. Google Sheets Setup (Optional)
The system remains functional without this, but logging will be disabled.
-   Follow the detailed instructions in [SHEETS.md](./SHEETS.md) to create a Service Account and `credentials.json`.
-   Share your "Doorbell Log" spreadsheet with the service account email.

---

## 🖥️ Usage

### Running the System
Start the main security loop and web server:
```bash
python main.py
```
-   **Dashboard:** Open `http://127.0.0.1:5000` in your browser.
-   **Admin Password:** Default is `admin123` (configurable in `main.py`).

### Adding New Faces
Register new individuals while the main system is running:
```bash
python add_face.py
```
-   **SPACE:** Capture frame.
-   **Name:** Enter the person's name in the terminal.
-   **R:** Retake.
-   **Q:** Quit.
-   *The main system will automatically detect the new face file and reload its database instantly.*

---

## 📂 Project Structure

-   `main.py`: The core application (Face recognition, Flask server, Arduino & Sheets integration).
-   `add_face.py`: Utility to capture and save new known faces.
-   `arduino_code/`: Contains the `.ino` file for the hardware controller.
-   `known_faces/`: Directory where registered face images are stored.
-   `templates/`: HTML files for the web dashboard.
-   `SHEETS.md`: Comprehensive guide for Google API setup.
-   `req.txt`: List of required Python packages.

---

## ⚙️ Configuration
You can customize the system behavior in the `CONFIG` section of `main.py`:
-   `PORT`: Change the Arduino COM port.
-   `TOLERANCE`: Adjust face recognition sensitivity (lower is stricter).
-   `ADMIN_PASSWORD`: Secure the web dashboard.
-   `LOG_COOLDOWN`: Minimum seconds between logging the same person.

---

## ⚖️ License
This project is provided for educational and personal use. Ensure you comply with local privacy laws regarding surveillance and data collection.
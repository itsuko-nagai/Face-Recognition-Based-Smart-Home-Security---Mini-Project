import serial
import time

PORT = "COM11"
BAUD = 9600

print(f"[INFO] Connecting to {PORT}...")
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)
print("[INFO] Connected!")

print("[INFO] Blinking LED 5 times...")
for i in range(5):
    print(f"  [{i+1}] LED ON")
    ser.write(b'1')
    time.sleep(1)
    print(f"  [{i+1}] LED OFF")
    ser.write(b'0')
    time.sleep(1)

ser.write(b'0')
ser.close()
print("[INFO] Done.")

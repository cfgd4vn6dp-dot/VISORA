import time
import threading
import requests
import cv2
import numpy as np
from ultralytics import YOLO

PI_URL = "http://10.96.80.129:8000/pi_camera_ai.jpg"

# Shared latest frame
latest_frame = None
latest_result = None
frame_lock = threading.Lock()

running = True


# ============================================================
# CAMERA THREAD
# Continuously downloads the newest frame
# ============================================================

def camera_thread():

    global latest_frame

    session = requests.Session()

    while running:

        try:

            response = session.get(
                PI_URL,
                timeout=1
            )

            response.raise_for_status()

            data = np.frombuffer(
                response.content,
                dtype=np.uint8
            )

            frame = cv2.imdecode(
                data,
                cv2.IMREAD_COLOR
            )

            if frame is not None:

                with frame_lock:
                    latest_frame = frame

        except Exception:
            time.sleep(0.01)


# ============================================================
# AI THREAD
# Processes only the newest available frame
# ============================================================

def ai_thread():

    global latest_result

    model = YOLO("yolo11n.pt")

    while running:

        with frame_lock:

            if latest_frame is None:
                continue

            frame = latest_frame.copy()

        try:

            results = model.predict(
                source=frame,
                device=0,
                imgsz=320,
                conf=0.35,
                half=True,
                verbose=False
            )

            with frame_lock:
                latest_result = results[0]

        except Exception as e:

            print("AI error:", e)


# ============================================================
# START THREADS
# ============================================================

print("==============================================")
print("       SIGHT-X LOW-LATENCY AI")
print("==============================================")
print("Camera : Raspberry Pi Camera V2")
print("AI     : YOLO11n")
print("GPU    : RTX 3050")
print("Mode   : Latest Frame")
print("Press Q to quit")
print("==============================================")


camera_worker = threading.Thread(
    target=camera_thread,
    daemon=True
)

ai_worker = threading.Thread(
    target=ai_thread,
    daemon=True
)

camera_worker.start()
ai_worker.start()


# ============================================================
# DISPLAY
# ============================================================

last_time = time.time()
display_fps = 0

while True:

    with frame_lock:

        if latest_frame is None:
            continue

        frame = latest_frame.copy()

        result = latest_result

    # Draw latest AI result onto newest camera frame
    if result is not None:

        display = result.plot()

    else:

        display = frame

    # FPS calculation
    now = time.time()

    if now != last_time:
        display_fps = 1 / (now - last_time)

    last_time = now

    cv2.putText(
        display,
        f"Display FPS: {display_fps:.1f}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (0, 255, 0),
        2
    )

    cv2.imshow(
        "SIGHT-X - Low Latency AI",
        display
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


running = False

cv2.destroyAllWindows()
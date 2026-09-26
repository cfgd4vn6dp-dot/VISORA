import cv2
import requests
import numpy as np
import threading
import time
from ultralytics import YOLO

# ============================================================
# SIGHT-X LIVE AI
# CAMERA + COLLISION WARNING + SIDE SAFETY PANEL
# ============================================================

PI_IMAGE_URL = "http://10.96.80.129:8000/pi_camera_ai.jpg"
PI_SENSOR_URL = "http://10.96.80.129:8001/sensor_data.json"

# ============================================================
# YOLO
# ============================================================

model = YOLO("yolo11n.pt")

# ============================================================
# SHARED DATA
# ============================================================

latest_frame = None
latest_result = None

latest_distance = 400.0
latest_motion = False

frame_lock = threading.Lock()
result_lock = threading.Lock()
sensor_lock = threading.Lock()

running = True


# ============================================================
# CAMERA THREAD
# ============================================================

def camera_worker():

    global latest_frame

    session = requests.Session()

    while running:

        try:

            response = session.get(
                PI_IMAGE_URL,
                timeout=2
            )

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

            time.sleep(0.05)


# ============================================================
# SENSOR THREAD
# ============================================================

def sensor_worker():

    global latest_distance
    global latest_motion

    session = requests.Session()

    while running:

        try:

            response = session.get(
                PI_SENSOR_URL,
                timeout=2
            )

            data = response.json()

            distance = data.get(
                "ultrasonic_cm",
                400.0
            )

            motion = data.get(
                "rcwl_motion",
                False
            )

            with sensor_lock:

                latest_distance = float(distance)
                latest_motion = bool(motion)

        except Exception:

            time.sleep(0.1)


# ============================================================
# AI THREAD
# ============================================================

def ai_worker():

    global latest_result

    while running:

        with frame_lock:

            if latest_frame is None:

                time.sleep(0.01)
                continue

            frame = latest_frame.copy()

        try:

            results = model.predict(
                source=frame,
                device=0,
                imgsz=320,
                conf=0.35,
                verbose=False
            )

            with result_lock:
                latest_result = results[0]

        except Exception as e:

            print("AI Error:", e)

            time.sleep(0.1)


# ============================================================
# START THREADS
# ============================================================

threading.Thread(
    target=camera_worker,
    daemon=True
).start()

threading.Thread(
    target=sensor_worker,
    daemon=True
).start()

threading.Thread(
    target=ai_worker,
    daemon=True
).start()


# ============================================================
# WINDOW
# ============================================================

window_name = "SIGHT-X - Live AI Camera"

cv2.namedWindow(
    window_name,
    cv2.WINDOW_NORMAL
)

cv2.resizeWindow(
    window_name,
    1400,
    760
)


# ============================================================
# FPS
# ============================================================

last_time = time.perf_counter()
display_fps = 0.0


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    # --------------------------------------------------------
    # CAMERA
    # --------------------------------------------------------

    with frame_lock:

        if latest_frame is None:

            time.sleep(0.01)
            continue

        camera = latest_frame.copy()


    # --------------------------------------------------------
    # SENSOR
    # --------------------------------------------------------

    with sensor_lock:

        distance = latest_distance
        motion = latest_motion


    # --------------------------------------------------------
    # AI RESULT
    # --------------------------------------------------------

    with result_lock:

        result = latest_result


    # ========================================================
    # DRAW YOLO
    # ========================================================

    detected_objects = []

    highest_risk = "SAFE"


    if result is not None:

        for box in result.boxes:

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )

            confidence = float(
                box.conf[0]
            )

            class_id = int(
                box.cls[0]
            )

            name = model.names[class_id]

            detected_objects.append(
                (name, confidence)
            )


            # ------------------------------------------------
            # RISK
            # ------------------------------------------------

            if name == "person":

                if distance <= 50:
                    risk = "DANGER"

                elif distance <= 150:
                    risk = "CAUTION"

                else:
                    risk = "SAFE"


            elif name in ["car", "truck", "bus"]:

                if distance <= 100:
                    risk = "DANGER"

                elif distance <= 250:
                    risk = "CAUTION"

                else:
                    risk = "SAFE"


            else:

                if distance <= 50:
                    risk = "DANGER"

                elif distance <= 150:
                    risk = "CAUTION"

                else:
                    risk = "SAFE"


            risk_order = {
                "SAFE": 0,
                "CAUTION": 1,
                "DANGER": 2
            }

            if risk_order[risk] > risk_order[highest_risk]:

                highest_risk = risk


            # ------------------------------------------------
            # BOX
            # ------------------------------------------------

            cv2.rectangle(
                camera,
                (x1, y1),
                (x2, y2),
                (0, 255, 0),
                2
            )

            label = (
                f"{name} "
                f"{confidence * 100:.0f}%"
            )

            cv2.putText(
                camera,
                label,
                (x1, max(y1 - 10, 25)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2
            )


    # ========================================================
    # WARNING
    # ========================================================

    if highest_risk == "DANGER":

        warning = "COLLISION WARNING"

    elif highest_risk == "CAUTION":

        warning = "OBJECT NEARBY"

    else:

        warning = "NO COLLISION WARNING"


    # ========================================================
    # FPS
    # ========================================================

    now = time.perf_counter()

    elapsed = now - last_time

    if elapsed > 0:

        instant_fps = 1.0 / elapsed

        if display_fps == 0:

            display_fps = instant_fps

        else:

            display_fps = (
                0.85 * display_fps
                + 0.15 * instant_fps
            )

    last_time = now


    # ========================================================
    # CREATE SIDE PANEL
    # ========================================================

    # Camera size
    camera_width = 960
    camera_height = 540

    camera_display = cv2.resize(
        camera,
        (camera_width, camera_height)
    )


    # Side panel
    panel_width = 400
    panel_height = camera_height

    panel = np.zeros(
        (panel_height, panel_width, 3),
        dtype=np.uint8
    )


    # ========================================================
    # PANEL CONTENT
    # ========================================================

    cv2.putText(
        panel,
        "SIGHT-X STATUS",
        (25, 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (0, 255, 255),
        2
    )

    cv2.putText(
        panel,
        "----------------------",
        (25, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        1
    )


    # Distance

    cv2.putText(
        panel,
        "HC-SR04 DISTANCE",
        (25, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    cv2.putText(
        panel,
        f"{distance:.1f} cm",
        (25, 145),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2
    )


    # Object

    cv2.putText(
        panel,
        "DETECTED OBJECT",
        (25, 185),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


    if detected_objects:

        object_name = detected_objects[0][0]
        object_conf = detected_objects[0][1]

        object_text = (
            f"{object_name} "
            f"{object_conf * 100:.0f}%"
        )

    else:

        object_text = "NONE"


    cv2.putText(
        panel,
        object_text,
        (25, 220),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )


    # Motion

    cv2.putText(
        panel,
        "RCWL MOTION",
        (25, 260),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


    motion_text = (
        "DETECTED"
        if motion
        else
        "NO MOTION"
    )


    cv2.putText(
        panel,
        motion_text,
        (25, 295),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.8,
        (255, 255, 255),
        2
    )


    # Risk

    cv2.putText(
        panel,
        "RISK LEVEL",
        (25, 335),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


    cv2.putText(
        panel,
        highest_risk,
        (25, 375),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (255, 255, 255),
        2
    )


    # Warning

    cv2.putText(
        panel,
        "WARNING",
        (25, 420),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


    cv2.putText(
        panel,
        warning,
        (25, 455),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 255),
        2
    )


    # FPS

    cv2.putText(
        panel,
        f"AI FPS : {display_fps:.1f}",
        (25, 500),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )


    cv2.putText(
        panel,
        "GPU : RTX 3050",
        (25, 530),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )


    # ========================================================
    # COMBINE CAMERA + PANEL
    # ========================================================

    final_screen = np.hstack(
        (camera_display, panel)
    )


    # ========================================================
    # SHOW
    # ========================================================

    cv2.imshow(
        window_name,
        final_screen
    )


    key = cv2.waitKey(1) & 0xFF

    if key == ord("q"):

        break


# ============================================================
# EXIT
# ============================================================

running = False

cv2.destroyAllWindows()

print("SIGHT-X Live AI stopped.")
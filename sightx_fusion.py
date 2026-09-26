import time
import threading
import requests
import cv2
import numpy as np
from ultralytics import YOLO

# ============================================================
# SIGHT-X : YOLO + HC-SR04 SENSOR FUSION
# ============================================================

PI_IMAGE_URL = "http://10.96.80.129:8000/pi_camera_ai.jpg"
PI_DATA_URL = "http://10.96.80.129:8001/sensor_data.json"

# ============================================================
# LOAD YOLO
# ============================================================

print("==========================================")
print("       SIGHT-X SENSOR FUSION")
print("==========================================")
print("Loading YOLO11n...")

model = YOLO("yolo11n.pt")

print("YOLO loaded successfully!")
print("Camera : Raspberry Pi Camera V2")
print("Sensor : HC-SR04")
print("AI     : YOLO11n")
print("GPU    : CUDA")
print("==========================================")

# ============================================================
# SHARED DATA
# ============================================================

latest_frame = None
latest_distance = None
latest_result = None

lock = threading.Lock()
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

                with lock:
                    latest_frame = frame

        except Exception:

            time.sleep(0.01)


# ============================================================
# HC-SR04 SENSOR THREAD
# ============================================================

def sensor_worker():

    global latest_distance

    session = requests.Session()

    while running:

        try:

            response = session.get(
                PI_DATA_URL,
                timeout=1
            )

            response.raise_for_status()

            data = response.json()

            distance = data.get("ultrasonic_cm")

            with lock:
                latest_distance = distance

        except Exception:

            time.sleep(0.1)


# ============================================================
# YOLO AI THREAD
# ============================================================

def ai_worker():

    global latest_result

    while running:

        with lock:

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

            with lock:
                latest_result = results[0]

        except Exception as e:

            print("AI Error:", e)

        time.sleep(0.01)


# ============================================================
# SMART RISK CLASSIFICATION
# ============================================================

def calculate_risk(distance, detected_objects):

    if distance is None:
        return "WAITING"

    if len(detected_objects) == 0:
        return "MONITOR"

    # --------------------------------------------------------
    # PERSON
    # --------------------------------------------------------

    if "person" in detected_objects:

        if distance <= 50:
            return "DANGER"

        elif distance <= 150:
            return "CAUTION"

        else:
            return "SAFE"

    # --------------------------------------------------------
    # VEHICLES
    # --------------------------------------------------------

    vehicle_objects = [
        "car",
        "truck",
        "bus"
    ]

    if any(
        vehicle in detected_objects
        for vehicle in vehicle_objects
    ):

        if distance <= 100:
            return "DANGER"

        elif distance <= 250:
            return "CAUTION"

        else:
            return "SAFE"

    # --------------------------------------------------------
    # OTHER OBJECTS
    # --------------------------------------------------------

    if distance <= 50:
        return "DANGER"

    elif distance <= 150:
        return "CAUTION"

    else:
        return "SAFE"


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
# DISPLAY
# ============================================================

while True:

    with lock:

        if latest_frame is None:
            continue

        frame = latest_frame.copy()
        result = latest_result
        distance = latest_distance

    detected_objects = []

    # --------------------------------------------------------
    # YOLO RESULTS
    # --------------------------------------------------------

    if result is not None:

        boxes = result.boxes

        for box in boxes:

            class_id = int(box.cls[0])

            object_name = model.names[class_id]

            detected_objects.append(
                object_name
            )

        display = result.plot()

    else:

        display = frame

    # Remove duplicate object names

    detected_objects = sorted(
        set(detected_objects)
    )

    # --------------------------------------------------------
    # DISTANCE DISPLAY
    # --------------------------------------------------------

    if distance is not None:

        cv2.putText(
            display,
            f"HC-SR04 Distance: {distance:.1f} cm",
            (10, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2
        )

    else:

        cv2.putText(
            display,
            "HC-SR04 Distance: WAITING",
            (10, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2
        )

    # --------------------------------------------------------
    # OBJECT DISPLAY
    # --------------------------------------------------------

    if detected_objects:

        object_text = ", ".join(
            detected_objects
        )

    else:

        object_text = "None"

    cv2.putText(
        display,
        f"Detected: {object_text}",
        (10, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    # --------------------------------------------------------
    # RISK
    # --------------------------------------------------------

    risk = calculate_risk(
        distance,
        detected_objects
    )

    # Choose display color

    if risk == "DANGER":

        risk_color = (0, 0, 255)

    elif risk == "CAUTION":

        risk_color = (0, 255, 255)

    elif risk == "SAFE":

        risk_color = (0, 255, 0)

    else:

        risk_color = (255, 255, 255)

    cv2.putText(
        display,
        f"RISK: {risk}",
        (10, 110),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        risk_color,
        3
    )

    # --------------------------------------------------------
    # WARNING
    # --------------------------------------------------------

    if risk == "DANGER":

        cv2.putText(
            display,
            "!!! COLLISION WARNING !!!",
            (10, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            3
        )

    elif risk == "CAUTION":

        cv2.putText(
            display,
            "CAUTION - OBJECT NEARBY",
            (10, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

    # --------------------------------------------------------
    # SHOW WINDOW
    # --------------------------------------------------------

    cv2.imshow(
        "SIGHT-X - AI + HC-SR04 Sensor Fusion",
        display
    )

    # Q = quit

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


# ============================================================
# STOP
# ============================================================

running = False

cv2.destroyAllWindows()

print("SIGHT-X stopped.")
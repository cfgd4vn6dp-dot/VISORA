import cv2
import requests
import numpy as np
import time

PI_URL = "http://10.96.80.129:8000/pi_camera_ai.jpg"

print("======================================")
print("       SIGHT-X LOW LATENCY VIEW")
print("======================================")
print("Camera : Raspberry Pi Camera V2")
print("Press Q to quit")
print("======================================")

session = requests.Session()

while True:

    try:
        response = session.get(
            PI_URL,
            timeout=1
        )

        data = np.frombuffer(
            response.content,
            dtype=np.uint8
        )

        frame = cv2.imdecode(
            data,
            cv2.IMREAD_COLOR
        )

        if frame is None:
            continue

        cv2.imshow(
            "SIGHT-X - Live Camera",
            frame
        )

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    except Exception as e:
        print("Connection error:", e)
        time.sleep(0.1)

cv2.destroyAllWindows()
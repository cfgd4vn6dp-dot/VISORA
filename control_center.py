import tkinter as tk
from tkinter import ttk
import requests
import threading
import time
import json

# ============================================================
# SIGHT-X CONTROL CENTER
# ============================================================

SENSOR_URL = "http://10.96.80.129:8001/sensor_data.json"

# ------------------------------------------------------------
# Window
# ------------------------------------------------------------

root = tk.Tk()
root.title("SIGHT-X CONTROL CENTER")
root.geometry("900x600")
root.resizable(False, False)

# ------------------------------------------------------------
# Variables
# ------------------------------------------------------------

gps_status = tk.StringVar(value="WAITING FOR GPS FIX")
latitude = tk.StringVar(value="--")
longitude = tk.StringVar(value="--")
satellites = tk.StringVar(value="--")

distance = tk.StringVar(value="-- cm")
motion = tk.StringVar(value="--")

pi_camera = tk.StringVar(value="--")
usb_camera = tk.StringVar(value="--")

timestamp = tk.StringVar(value="--")
connection = tk.StringVar(value="CONNECTING...")

# ------------------------------------------------------------
# Title
# ------------------------------------------------------------

title = tk.Label(
    root,
    text="SIGHT-X CONTROL CENTER",
    font=("Arial", 24, "bold")
)
title.pack(pady=15)

subtitle = tk.Label(
    root,
    text="Mining Vehicle Safety & Synthetic Visibility System",
    font=("Arial", 11)
)
subtitle.pack()

# ------------------------------------------------------------
# Main frame
# ------------------------------------------------------------

main = tk.Frame(root)
main.pack(fill="both", expand=True, padx=25, pady=20)

# ------------------------------------------------------------
# GPS section
# ------------------------------------------------------------

gps_frame = ttk.LabelFrame(main, text=" VEHICLE GPS ", padding=15)
gps_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

tk.Label(gps_frame, text="GPS Status:", font=("Arial", 11, "bold")).grid(
    row=0, column=0, sticky="w", pady=5
)

tk.Label(gps_frame, textvariable=gps_status, font=("Arial", 11)).grid(
    row=0, column=1, sticky="w", pady=5
)

tk.Label(gps_frame, text="Latitude:", font=("Arial", 11, "bold")).grid(
    row=1, column=0, sticky="w", pady=5
)

tk.Label(gps_frame, textvariable=latitude, font=("Arial", 11)).grid(
    row=1, column=1, sticky="w", pady=5
)

tk.Label(gps_frame, text="Longitude:", font=("Arial", 11, "bold")).grid(
    row=2, column=0, sticky="w", pady=5
)

tk.Label(gps_frame, textvariable=longitude, font=("Arial", 11)).grid(
    row=2, column=1, sticky="w", pady=5
)

tk.Label(gps_frame, text="Satellites:", font=("Arial", 11, "bold")).grid(
    row=3, column=0, sticky="w", pady=5
)

tk.Label(gps_frame, textvariable=satellites, font=("Arial", 11)).grid(
    row=3, column=1, sticky="w", pady=5
)

# ------------------------------------------------------------
# Sensor section
# ------------------------------------------------------------

sensor_frame = ttk.LabelFrame(main, text=" SENSOR STATUS ", padding=15)
sensor_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

tk.Label(sensor_frame, text="HC-SR04 Distance:", font=("Arial", 11, "bold")).grid(
    row=0, column=0, sticky="w", pady=5
)

tk.Label(sensor_frame, textvariable=distance, font=("Arial", 11)).grid(
    row=0, column=1, sticky="w", pady=5
)

tk.Label(sensor_frame, text="RCWL Motion:", font=("Arial", 11, "bold")).grid(
    row=1, column=0, sticky="w", pady=5
)

tk.Label(sensor_frame, textvariable=motion, font=("Arial", 11)).grid(
    row=1, column=1, sticky="w", pady=5
)

tk.Label(sensor_frame, text="Pi Camera:", font=("Arial", 11, "bold")).grid(
    row=2, column=0, sticky="w", pady=5
)

tk.Label(sensor_frame, textvariable=pi_camera, font=("Arial", 11)).grid(
    row=2, column=1, sticky="w", pady=5
)

tk.Label(sensor_frame, text="USB Camera:", font=("Arial", 11, "bold")).grid(
    row=3, column=0, sticky="w", pady=5
)

tk.Label(sensor_frame, textvariable=usb_camera, font=("Arial", 11)).grid(
    row=3, column=1, sticky="w", pady=5
)

# ------------------------------------------------------------
# Connection section
# ------------------------------------------------------------

status_frame = ttk.LabelFrame(main, text=" SYSTEM STATUS ", padding=15)
status_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

tk.Label(
    status_frame,
    text="Raspberry Pi Connection:",
    font=("Arial", 11, "bold")
).grid(row=0, column=0, sticky="w", padx=10)

tk.Label(
    status_frame,
    textvariable=connection,
    font=("Arial", 11)
).grid(row=0, column=1, sticky="w", padx=10)

tk.Label(
    status_frame,
    text="Last Update:",
    font=("Arial", 11, "bold")
).grid(row=1, column=0, sticky="w", padx=10, pady=5)

tk.Label(
    status_frame,
    textvariable=timestamp,
    font=("Arial", 11)
).grid(row=1, column=1, sticky="w", padx=10, pady=5)

# ------------------------------------------------------------
# GPS MAP AREA
# ------------------------------------------------------------

map_frame = ttk.LabelFrame(main, text=" VEHICLE LOCATION ", padding=10)
map_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

map_text = tk.Label(
    map_frame,
    text=(
        "GPS MAP\n\n"
        "Waiting for GPS satellite fix...\n\n"
        "When the GPS gets a valid position,\n"
        "the vehicle latitude and longitude will appear here."
    ),
    font=("Arial", 12),
    justify="center"
)

map_text.pack(pady=15)

# ------------------------------------------------------------
# Read GPS information
# ------------------------------------------------------------

def get_gps_info(data):

    gps = data.get("gps", {})

    lat = gps.get("latitude")
    if lat is None:
        lat = gps.get("lat")

    lon = gps.get("longitude")
    if lon is None:
        lon = gps.get("lon")

    sats = gps.get("satellites")
    if sats is None:
        sats = gps.get("num_satellites")

    return lat, lon, sats


# ------------------------------------------------------------
# Update dashboard
# ------------------------------------------------------------

def update_dashboard():

    while True:

        try:

            response = requests.get(
                SENSOR_URL,
                timeout=3
            )

            data = response.json()

            connection.set("CONNECTED")

            # ---------------- GPS ----------------

            lat, lon, sats = get_gps_info(data)

            if lat is not None and lon is not None:

                gps_status.set("GPS FIXED")
                latitude.set(str(lat))
                longitude.set(str(lon))

                if sats is not None:
                    satellites.set(str(sats))

                map_text.config(
                    text=(
                        "GPS LOCATION AVAILABLE\n\n"
                        f"Latitude  : {lat}\n"
                        f"Longitude : {lon}\n\n"
                        "Vehicle position received."
                    )
                )

            else:

                gps_status.set("WAITING FOR GPS FIX")
                latitude.set("--")
                longitude.set("--")

                if sats is not None:
                    satellites.set(str(sats))
                else:
                    satellites.set("0")

                map_text.config(
                    text=(
                        "GPS MAP\n\n"
                        "Waiting for GPS satellite fix...\n\n"
                        "No valid vehicle coordinates yet."
                    )
                )

            # ---------------- Ultrasonic ----------------

            ultrasonic = data.get("ultrasonic_cm")

            if ultrasonic is not None:
                distance.set(f"{ultrasonic:.1f} cm")
            else:
                distance.set("-- cm")

            # ---------------- RCWL ----------------

            rcwl = data.get("rcwl_motion")

            if rcwl is True:
                motion.set("DETECTED")
            else:
                motion.set("NO MOTION")

            # ---------------- Cameras ----------------

            cameras = data.get("cameras", {})

            if cameras.get("pi_camera"):
                pi_camera.set("OK")
            else:
                pi_camera.set("OFF")

            if cameras.get("usb_camera"):
                usb_camera.set("OK")
            else:
                usb_camera.set("OFF")

            # ---------------- Timestamp ----------------

            timestamp.set(
                str(data.get("timestamp", "--"))
            )

        except Exception:

            connection.set("DISCONNECTED")

        time.sleep(1)


# ------------------------------------------------------------
# Start background data reader
# ------------------------------------------------------------

thread = threading.Thread(
    target=update_dashboard,
    daemon=True
)

thread.start()

# ------------------------------------------------------------
# Start GUI
# ------------------------------------------------------------

root.mainloop()
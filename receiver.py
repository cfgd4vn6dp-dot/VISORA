import socket
import json

HOST = "0.0.0.0"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server.bind((HOST, PORT))
server.listen(1)

print("===================================")
print("       SIGHT-X LAPTOP RECEIVER")
print("===================================")
print(f"Listening on port {PORT}...")
print("Waiting for Raspberry Pi...")
print()

conn, address = server.accept()

print("Connected to:", address)
print()

buffer = ""

try:
    while True:
        data = conn.recv(4096)

        if not data:
            print("Raspberry Pi disconnected.")
            break

        buffer += data.decode("utf-8")

        while "\n" in buffer:
            message, buffer = buffer.split("\n", 1)

            if message.strip():
                try:
                    sensor_data = json.loads(message)

                    print("-----------------------------------")
                    print("SIGHT-X DATA RECEIVED")
                    print("-----------------------------------")
                    print(json.dumps(sensor_data, indent=2))

                except json.JSONDecodeError:
                    print("Received:", message)

except KeyboardInterrupt:
    print("\nReceiver stopped.")

finally:
    conn.close()
    server.close()
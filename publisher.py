"""
publisher.py — Arduino → MQTT Publisher
========================================
1. Scans all COM ports and finds the Arduino automatically
2. Reads temperature values from it over serial
3. Publishes each value to the MQTT broker
4. Prints every reading to the console

Run:
    python publisher.py

This script is fully independent from the backend.
Run it in its own terminal window.
"""

import sys
import time
import serial
import serial.tools.list_ports
import paho.mqtt.client as mqtt

# ── CONFIG ────────────────────────────────────────────────────────────────────
BAUD_RATE    = 9600
MQTT_BROKER  = "157.173.101.159"
MQTT_PORT    = 1883
MQTT_TOPIC   = "spe/temperature"
MQTT_CLIENT_ID = "arduino-publisher"

# ── MQTT setup ────────────────────────────────────────────────────────────────
mqtt_connected = False

def on_connect(client, userdata, flags, rc):
    global mqtt_connected
    if rc == 0:
        mqtt_connected = True
        print(f"[MQTT]   Connected to {MQTT_BROKER}:{MQTT_PORT}")
        print(f"[MQTT]   Publishing to topic: {MQTT_TOPIC}")
    else:
        print(f"[MQTT]   Connection failed (rc={rc})")
        sys.exit(1)

def on_disconnect(client, userdata, rc):
    global mqtt_connected
    mqtt_connected = False
    if rc != 0:
        print(f"[MQTT]   Disconnected unexpectedly (rc={rc}), reconnecting...")

def on_publish(client, userdata, mid):
    pass  # silent — main loop already prints each reading

# ── Find Arduino COM port ─────────────────────────────────────────────────────
def find_arduino_port():
    """
    Scan all available COM ports and return the first one that looks
    like an Arduino (matches common USB-serial chip descriptions).
    If none is identified automatically, list all ports and let the
    user pick one.
    """
    ports = list(serial.tools.list_ports.comports())

    if not ports:
        print("[Serial] No COM ports found. Is the Arduino plugged in?")
        sys.exit(1)

    print("[Serial] Available ports:")
    for p in ports:
        print(f"         {p.device:10}  {p.description}")

    # Keywords that appear in Arduino / USB-serial chip descriptions
    arduino_keywords = [
        "arduino", "ch340", "ch341", "cp210", "ftdi",
        "usb serial", "usb-serial", "uart", "uno"
    ]

    for p in ports:
        desc = p.description.lower()
        if any(kw in desc for kw in arduino_keywords):
            print(f"\n[Serial] Auto-detected Arduino on {p.device} ({p.description})")
            return p.device

    # No auto-match — ask the user
    print("\n[Serial] Could not auto-detect Arduino.")
    print("         Enter the port name from the list above (e.g. COM3, COM7):")
    port = input("         > ").strip()
    return port


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print()
    print("=" * 55)
    print("  Arduino → MQTT Publisher")
    print("=" * 55)
    print(f"  Broker : {MQTT_BROKER}:{MQTT_PORT}")
    print(f"  Topic  : {MQTT_TOPIC}")
    print("=" * 55)
    print()

    # ── Connect to MQTT broker ────────────────────────────────
    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish    = on_publish

    print("[MQTT]   Connecting to broker...")
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except Exception as e:
        print(f"[MQTT]   Cannot reach broker: {e}")
        sys.exit(1)

    client.loop_start()

    # Wait until MQTT is connected before opening serial
    deadline = time.time() + 10
    while not mqtt_connected and time.time() < deadline:
        time.sleep(0.1)

    if not mqtt_connected:
        print("[MQTT]   Timed out waiting for broker connection.")
        sys.exit(1)

    # ── Find and open Arduino serial port ────────────────────
    port = find_arduino_port()
    print(f"\n[Serial] Opening {port} at {BAUD_RATE} baud...")

    try:
        ser = serial.Serial(port, BAUD_RATE, timeout=3)
    except serial.SerialException as e:
        print(f"[Serial] Failed to open {port}: {e}")
        sys.exit(1)

    # Arduino resets on DTR — wait for it to boot
    time.sleep(2)
    ser.reset_input_buffer()
    print(f"[Serial] Ready. Waiting for data (Ctrl+C to stop)...\n")
    print(f"  {'#':<6} {'Value':<15} {'Published'}")
    print("  " + "-" * 40)

    count = 0

    try:
        while True:
            raw = ser.readline()
            if not raw:
                continue  # serial timeout, no data yet

            try:
                line = raw.decode("utf-8").strip()
            except UnicodeDecodeError:
                continue  # skip garbled bytes

            if not line:
                continue

            # Skip non-numeric startup messages
            try:
                value = float(line)
            except ValueError:
                print(f"  [info] {line}")
                continue

            count += 1
            payload = f"{value:.2f}"
            result  = client.publish(MQTT_TOPIC, payload, qos=1)

            status = "OK" if result.rc == mqtt.MQTT_ERR_SUCCESS else f"ERR rc={result.rc}"
            print(f"  {count:<6} {payload + ' C':<15} {status}")

    except KeyboardInterrupt:
        print(f"\n\n  Stopped. Total readings published: {count}")

    finally:
        client.loop_stop()
        client.disconnect()
        ser.close()
        print("  Connections closed.")


if __name__ == "__main__":
    main()

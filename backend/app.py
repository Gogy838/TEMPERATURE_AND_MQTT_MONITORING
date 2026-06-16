"""
Flask backend — SPE Temperature Monitor
========================================
Subscribes to the MQTT broker and serves:
  GET /          → live dashboard (HTML page)
  GET /api/data  → last N readings as JSON

Run:
    pip install -r requirements.txt
    python app.py

Then open http://localhost:5000 in your browser.
"""

import threading
from collections import deque
from datetime import datetime

import paho.mqtt.client as mqtt
from flask import Flask, jsonify, render_template

# ─── MQTT config ─────────────────────────────────────────────────────────────
MQTT_BROKER   = "157.173.101.159"
MQTT_PORT     = 1883
MQTT_TOPIC    = "spe/temperature"
MQTT_CLIENT_ID = "flask-dashboard-subscriber"

# ─── Data store ───────────────────────────────────────────────────────────────
MAX_POINTS = 100          # keep the last 100 readings in memory
data_lock  = threading.Lock()
readings   = deque(maxlen=MAX_POINTS)   # each item: {"time": str, "temp": float}

mqtt_status = {"connected": False, "last_error": None}

# ─── MQTT callbacks ───────────────────────────────────────────────────────────

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        mqtt_status["connected"] = True
        mqtt_status["last_error"] = None
        print(f"[MQTT] Connected to {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        print(f"[MQTT] Subscribed to {MQTT_TOPIC}")
    else:
        codes = {1: "bad protocol", 2: "bad client id",
                 3: "unavailable", 4: "bad credentials", 5: "not authorised"}
        err = codes.get(rc, f"rc={rc}")
        mqtt_status["connected"] = False
        mqtt_status["last_error"] = err
        print(f"[MQTT] Connection failed — {err}")


def on_disconnect(client, userdata, rc):
    mqtt_status["connected"] = False
    if rc != 0:
        print(f"[MQTT] Unexpected disconnect (rc={rc}), will auto-reconnect …")


def on_message(client, userdata, msg):
    try:
        value = float(msg.payload.decode("utf-8").strip())
    except (ValueError, UnicodeDecodeError):
        return                      # ignore garbled messages

    timestamp = datetime.now().strftime("%H:%M:%S")
    with data_lock:
        readings.append({"time": timestamp, "temp": round(value, 2)})

    print(f"[MQTT] {timestamp}  {value:.2f} °C")


# ─── MQTT background thread ───────────────────────────────────────────────────

def start_mqtt():
    client = mqtt.Client(client_id=MQTT_CLIENT_ID)
    client.on_connect    = on_connect
    client.on_disconnect = on_disconnect
    client.on_message    = on_message

    # reconnect_delay_set: wait 1-30 s between reconnection attempts
    client.reconnect_delay_set(min_delay=1, max_delay=30)

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
    except Exception as e:
        mqtt_status["last_error"] = str(e)
        print(f"[MQTT] Cannot connect: {e}")

    # loop_forever handles reconnections automatically
    client.loop_forever()


# ─── Flask app ────────────────────────────────────────────────────────────────

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html",
                           broker=MQTT_BROKER,
                           port=MQTT_PORT,
                           topic=MQTT_TOPIC)


@app.route("/api/data")
def api_data():
    with data_lock:
        snapshot = list(readings)

    connected = mqtt_status["connected"]
    last_error = mqtt_status["last_error"]

    return jsonify({
        "connected": connected,
        "last_error": last_error,
        "count": len(snapshot),
        "readings": snapshot          # [{time, temp}, …]
    })


# ─── Entry point ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Start MQTT subscriber in a daemon thread so it dies with the process
    t = threading.Thread(target=start_mqtt, daemon=True)
    t.start()
    print("[Flask] Starting server on http://localhost:5000")
    # use_reloader=False is required when running background threads
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)

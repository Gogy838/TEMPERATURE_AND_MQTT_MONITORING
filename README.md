# SPE Temperature Monitor

**Trade Code: SPE — Embedded Systems Software Integration**

Reads temperature from an Arduino Uno, displays it on a 16×2 LCD, publishes
readings to an MQTT broker, and visualises them on a live Flask dashboard.

---

## How it works

```
┌─────────────┐        ┌──────────────┐   I²C   ┌──────────────┐
│  LM35       │──A0───▶│  Arduino Uno │────────▶│  16×2 LCD    │
│  sensor     │        │              │         └──────────────┘
└─────────────┘        │  serial out  │
                       └──────┬───────┘
                              │  USB serial (9600 baud)
                              ▼
                       ┌──────────────┐
                       │ publisher.py │  reads serial → publishes to MQTT
                       └──────┬───────┘
                              │  MQTT  topic: spe/temperature
                              ▼
                       ┌──────────────┐
                       │ MQTT broker  │  157.173.101.159:1883
                       └──────┬───────┘
                              │  MQTT subscribe
                              ▼
                       ┌──────────────┐
                       │  backend/    │  Flask app → http://localhost:5000
                       │  app.py      │  live graph, stats, readings log
                       └──────────────┘
```

---

## Project structure

```
temperatureDisplayAndMQTTMonitoring/
│
├── temperature_lcd/
│   └── temperature_lcd.ino   # Arduino sketch — upload once to the board
│
├── publisher.py              # Script 1: Arduino serial → MQTT broker
│
├── backend/
│   ├── app.py                # Script 2: MQTT subscriber + Flask dashboard
│   ├── requirements.txt      # Python dependencies
│   └── templates/
│       └── index.html        # Dashboard page (served by Flask)
│
├── docs/
│   └── wiring.md             # Hardware wiring reference
│
└── README.md
```

---

## Hardware required

| Component              | Notes                          |
|------------------------|--------------------------------|
| Arduino Uno            | Any revision                   |
| LM35 temperature sensor| Analog output, 10 mV/°C        |
| 16×2 LCD (I2C backpack)| I2C address 0x27 or 0x3F       |
| USB A-to-B cable       | Arduino ↔ PC                   |
| Jumper wires + breadboard |                             |

See `docs/wiring.md` for the full wiring diagram.

---

## Setup

### Step 1 — Upload the Arduino sketch

1. Open `temperature_lcd/temperature_lcd.ino` in the Arduino IDE.
2. Install the **LiquidCrystal I2C** library (by Frank de Brabander) via
   Sketch → Include Library → Manage Libraries.
3. Edit the candidate name on the relevant line:
   ```cpp
   const char CANDIDATE_NAME[] = "Your Name Here";
   ```
4. Select **Tools → Board → Arduino Uno** and the correct port.
5. Click **Upload**.

### Step 2 — Install Python dependencies

```
pip install pyserial paho-mqtt flask
```

Or use the backend requirements file:

```
pip install -r backend/requirements.txt
```

> pyserial and paho-mqtt are also needed by publisher.py — install them once
> and both scripts will work.

---

## Running the system

The publisher and the backend are **completely independent**.
Run each in its own terminal.

### Terminal 1 — Publisher (Arduino → MQTT)

```
python publisher.py
```

- Scans all COM ports and auto-detects the Arduino by its USB-serial chip
  (CH340, CP210x, FTDI, etc.).
- If it cannot auto-detect, it lists available ports and asks you to type one.
- Reads every temperature line from serial and publishes it to the broker.

Example output:
```
=======================================================
  Arduino → MQTT Publisher
=======================================================
  Broker : 157.173.101.159:1883
  Topic  : spe/temperature
=======================================================

[MQTT]   Connected to 157.173.101.159:1883
[Serial] Auto-detected Arduino on COM7 (USB-SERIAL CH340)
[Serial] Ready. Waiting for data (Ctrl+C to stop)...

  #      Value           Published
  ----------------------------------------
  1      25.31 C         OK
  2      25.63 C         OK
```

### Terminal 2 — Backend (MQTT → Dashboard)

```
cd backend
python app.py
```

- Subscribes to the broker topic `spe/temperature`.
- Stores the last 100 readings in memory.
- Serves the live dashboard at **http://localhost:5000**.

The backend works independently — it does not need the publisher to be running
to start, and the publisher does not need the backend.

---

## Dashboard

Open **http://localhost:5000** in your browser.

- **Current / Min / Max** stat cards — update every second, show 0 when no
  data has arrived yet.
- **Temperature graph** — Chart.js line chart of the last 100 readings,
  scales automatically to real data.
- **Raw readings log** — every received value with its timestamp.
- **Connection pill** — shows MQTT broker status (Connected / Disconnected).

---

## Configuration

| File            | Setting        | Default              |
|-----------------|----------------|----------------------|
| `publisher.py`  | `MQTT_BROKER`  | `157.173.101.159`    |
| `publisher.py`  | `MQTT_PORT`    | `1883`               |
| `publisher.py`  | `MQTT_TOPIC`   | `spe/temperature`    |
| `publisher.py`  | `BAUD_RATE`    | `9600`               |
| `backend/app.py`| `MQTT_BROKER`  | `157.173.101.159`    |
| `backend/app.py`| `MQTT_PORT`    | `1883`               |
| `backend/app.py`| `MQTT_TOPIC`   | `spe/temperature`    |

Both files have a `CONFIG` block at the top — edit there only.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| publisher.py: no ports found | Arduino not plugged in | Check USB cable |
| publisher.py: can't open port | Wrong port / driver missing | Install CH340 driver |
| Values ~170 °C | Sensor wired to 3.3V or backwards | Check wiring in `docs/wiring.md` |
| LCD blank (backlight on) | Wrong I2C address | Try `LCD_ADDR 0x3F` in the sketch |
| Dashboard shows 0 forever | Broker unreachable or publisher not running | Check broker IP and run publisher.py |
| MQTT connection refused | Broker not running on VPS | `sudo systemctl start mosquitto` on VPS |

---

## License

For educational use — SPE (Embedded Systems Software Integration) assessment.

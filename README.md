# 📡 Project Radar

> **Arduino-based ultrasonic radar with a real-time tactical HUD.**

Project Radar is an open-source Arduino + Python radar system that combines a servo-mounted ultrasonic sensor with a custom desktop visualization interface.

The Arduino continuously sweeps the sensor across a **0°–180° field of view**, measures distance, and streams telemetry over Serial. A Python desktop application receives that telemetry and renders it as a real-time radar display with scanning animation, detected targets, live logs, telemetry metrics, graphs, and a tactical-style HUD.

The goal of this project is not to reproduce military radar technology, but to build an impressive and practical radar-like visualization system using accessible electronics and a desktop interface.

---

## ✨ Features

### Hardware / Arduino

* 🔄 Automatic servo scanning from **0° to 180°**
* 📏 Ultrasonic distance measurement
* 🎯 Real-time angle + distance telemetry
* 🎛️ Manual servo control
* ↔️ Adjustable maximum detection range
* 💾 Scan position persistence using Arduino EEPROM
* 🔊 Buzzer feedback when an object is detected
* 💻 Serial communication with the Python application
* ⚡ Non-blocking timing-based control for servo movement and measurement

The default maximum range is **20 cm**, while the firmware allows the configured range to be adjusted between **10 cm and 100 cm** through Serial commands.

---

## 🖥️ Python Tactical HUD

The desktop application provides a futuristic radar-style interface designed around live sensor telemetry.

### Interface

* 🟢 Animated radar sweep
* 🎯 Real-time target markers
* 📍 Angle and distance visualization
* 📡 Live telemetry stream
* 📊 Signal analysis graph
* 📈 Scan activity graph
* ⚙️ System metrics
* 🧮 Target counter
* 🧭 Current scan angle
* 📏 Current measured distance
* 🔴 Visual target detection state
* 🟡 Search-state visualization
* 🔵 Manual-control state
* 💻 Matrix-style background animation
* 🖥️ Fixed-size desktop HUD layout

The interface is implemented with **Python Tkinter** and communicates with the Arduino using **PySerial**.

---

## 🧠 How It Works

The system is divided into two main components:

```text
┌──────────────────────┐
│      Arduino UNO     │
│                      │
│  Servo Motor         │
│      │               │
│      ▼               │
│  Ultrasonic Sensor   │
│      │               │
│      ▼               │
│ Distance Measurement │
│      │               │
│      ▼               │
│   Serial Telemetry   │
└──────────┬───────────┘
           │ USB Serial
           ▼
┌──────────────────────┐
│     Python HUD       │
│                      │
│ Serial Worker        │
│      │               │
│      ▼               │
│ Telemetry Processing │
│      │               │
│      ▼               │
│ Radar Visualization  │
│      │               │
│      ├── Target View  │
│      ├── Live Logs    │
│      ├── Metrics      │
│      └── Graphs       │
└──────────────────────┘
```

The Arduino measures the distance at the current servo angle and sends the result through Serial.

The Python application receives the stream in a dedicated background thread, places incoming data into a queue, and processes it without blocking the graphical interface.

---

## 🔌 Hardware

The current firmware uses the following connections:

| Component       | Arduino Pin |
| --------------- | ----------: |
| Servo Signal    |          D6 |
| Ultrasonic TRIG |          D9 |
| Ultrasonic ECHO |         D10 |
| Buzzer          |          D8 |

### Required Components

* Arduino board compatible with the `Servo` library
* Servo motor
* Ultrasonic distance sensor
* Buzzer
* Jumper wires
* Breadboard / suitable mounting
* USB cable

> The exact servo and ultrasonic sensor models are not hard-coded by the firmware, so compatible components can be used as long as the electrical interface matches.

---

## 📐 Arduino Pinout

```text
Arduino
│
├── D6  ───────── Servo Signal
│
├── D9  ───────── Ultrasonic TRIG
│
├── D10 ───────── Ultrasonic ECHO
│
└── D8  ───────── Buzzer
```

Make sure all components share a common **GND**.

---

## 📡 Serial Protocol

The Python application currently expects telemetry containing:

```text
ANGLE:<angle>,DIST:<distance>
```

Example:

```text
ANGLE:90,DIST:14.7
```

When no valid object is detected, the Arduino sends:

```text
ANGLE:90,DIST:-1
```

The Python application also contains support for additional telemetry fields such as:

```text
MODE:<mode>,ANGLE:<angle>,DIST:<distance>,TARGET:<angle>
```

This allows the HUD to support richer telemetry states and future firmware features.

---

## 🎛️ Controls

The Python HUD supports keyboard interaction.

| Key | Action                          |
| --- | ------------------------------- |
| `M` | Toggle manual control           |
| `←` | Move servo left in manual mode  |
| `→` | Move servo right in manual mode |
| `↑` | Increase maximum radar range    |
| `↓` | Decrease maximum radar range    |

The maximum range is adjustable from **10 cm to 100 cm**.

---

## 💾 EEPROM Persistence

The Arduino stores the current servo angle in EEPROM.

This means the last scan position can survive a restart or power cycle.

The firmware periodically updates the stored position using:

```cpp
EEPROM.update(EEPROM_ADDR, angle);
```

`EEPROM.update()` is used instead of blindly writing the value every cycle, helping avoid unnecessary EEPROM writes.

---

## 🐍 Python Requirements

The Python application requires:

* Python 3
* Tkinter
* PySerial

Install PySerial with:

```bash
pip install pyserial
```

On Linux, Tkinter may need to be installed separately:

```bash
sudo apt install python3-tk
```

---

## 🚀 Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/project-radar.git
cd project-radar
```

### 2. Upload the Arduino firmware

Open:

```text
radar.ino
```

in the Arduino IDE and upload it to your board.

### 3. Configure the Serial Port

Open:

```text
radar.py
```

and change:

```python
SERIAL_PORT = "COM8"
```

to the Serial port used by your Arduino.

For example:

```python
SERIAL_PORT = "COM3"
```

or on Linux:

```python
SERIAL_PORT = "/dev/ttyUSB0"
```

The baud rate must remain synchronized with the Arduino:

```text
9600 baud
```

### 4. Run the HUD

```bash
python radar.py
```

---

## 📁 Project Structure

```text
project-radar/
│
├── radar.ino
├── radar.py
├── README.md
├── LICENSE
└── assets/
    └── screenshots/
```

### Files

**`radar.ino`**

Arduino firmware responsible for servo control, ultrasonic measurements, buzzer feedback, EEPROM persistence, and Serial telemetry.

**`radar.py`**

Desktop visualization application responsible for Serial communication, telemetry processing, radar rendering, target visualization, live logs, graphs, and HUD animations.

**`assets/`**

Project screenshots, diagrams, and other documentation assets.

---

## 🧪 Current System

The current implementation is intentionally split between real sensor telemetry and interface-side visualization.

The following data comes directly from the Arduino:

* Scan angle
* Measured distance
* Detection state based on the configured range

The Python interface also contains visualization and analytics components intended to make the telemetry easier to interpret and provide a foundation for future radar features.

This architecture makes it possible to improve the firmware and visualization independently.

---

## 🔭 Future Ideas

Project Radar can be extended significantly.

Possible future improvements include:

* 🎯 More advanced target tracking
* 🧠 Real target persistence and identification
* 📡 Richer Serial telemetry protocol
* 🛰️ Multiple target tracking
* 📊 Real sensor-quality analysis
* 📈 Historical telemetry recording
* 💾 CSV/JSON telemetry export
* 🖥️ Cross-platform serial-port configuration
* ⚙️ Automatic Serial-port detection
* 🎛️ Configurable scan speed
* 🔊 Configurable detection alerts
* 🌐 Remote telemetry over Wi-Fi
* 📱 Web-based radar dashboard
* 🔌 ESP32-based wireless version
* 🗺️ Multi-sensor tracking experiments

---

## ⚠️ Limitations

This project is an experimental ultrasonic radar-style system.

It does **not** behave like electromagnetic radar and is limited by the range, field of view, response time, accuracy, and physical characteristics of the ultrasonic sensor and servo mechanism.

The visualization is designed to represent sensor measurements in a radar-like interface rather than provide radar-grade tracking.

---

## 🤝 Contributing

Contributions, improvements, experiments, and hardware adaptations are welcome.

A good contribution should ideally include:

* A clear description of the change
* Reproducible steps
* Updated documentation when necessary
* Clean and readable code
* Hardware changes documented clearly

Fork the repository, make your changes, and open a Pull Request.

---

## 📜 License

This project is open source.

See the `LICENSE` file for the terms under which the project is distributed.

---

## ⭐ Support

If you found the project interesting, consider giving the repository a ⭐.

It helps the project get discovered and encourages further development.

---

<div align="center">

**PROJECT // RADAR**

*Sense. Scan. Visualize.*

</div>

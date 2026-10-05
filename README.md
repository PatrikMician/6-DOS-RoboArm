# RoboArm v1.0 – 6-DOF Robotic Arm

An open-source 6-axis robotic arm powered by **Arduino**, featuring I2C servo driving (**PCA9685**), real-time **LCD status display**, physical **joystick controls**, and a **Python web interface** (Flask + pyserial) for controlling the arm from your browser over USB.

---

## Features

* **6 Degrees of Freedom (6-DOF):** Full control over base rotation, shoulder, forearm, wrist tilt, wrist rotation, and gripper.
* **Dual Control Modes:**
  * **Physical Joysticks:** Tactile control using two 2-axis analog joysticks with pushbuttons.
  * **Web Interface:** A small Python (Flask) server talks to the Arduino over USB serial; you control the arm from any browser. The web page contains **no JavaScript**.
* **Real-time LCD Feedback:** 16x2 I2C display shows current angles for the servos $S_1$ to $S_5$ and operational messages.
* **Smart Motion Control:** Smooth stepping for servo protection, EEPROM position saving, and an automated routine ("Dance mode").
* **Simulation mode:** try the web interface without any hardware.

---

## 🛠️ Hardware Requirements

| Component | Quantity | Description |
| :--- | :---: | :--- |
| **Arduino (Nano / Uno / Every)** | 1 | Main microcontroller |
| **PCA9685 PWM Driver** | 1 | 16-Channel 12-bit I2C Servo Driver (`0x40`) |
| **16x2 LCD with I2C Adapter** | 1 | Character display (`0x27`) |
| **Analog Joystick Modules** | 2 | Dual-axis joysticks with pushbuttons (e.g., KY-023) |
| **Servomotors** | 6 | Standard 180° servos (e.g., MG996R or SG90) |
| **External 5V Power Supply** | 1 | Dedicated high-current power supply for servos |

The website (`index.html`) also contains a parts list with shopping links.

---

## Software Requirements

* **Arduino IDE** (to upload the firmware)
* **Python 3.9 or newer** – [python.org/downloads](https://www.python.org/downloads/) (on Windows tick *"Add Python to PATH"* during installation)
* A USB cable and, for most Nano clones, the **CH340/CH341 driver** (included in `zip-soubory/CH34x_Install_Windows_v3_4.zip`)

---

## Quick Start Guide

### 1. Hardware Assembly & Wiring

1. Mount the servos to your 6-DOF robotic arm frame and connect them to the **PCA9685** channels **0–5** (see the servo table below).
2. Connect the **PCA9685** driver and the **I2C LCD** to the Arduino via the I2C bus:

   | Module pin | Arduino |
   | :--- | :--- |
   | GND | GND |
   | VCC | 5V |
   | SDA | A4 |
   | SCL | A5 |

3. Connect the joysticks:

   | Joystick | VCC | GND | VRx | VRy | SW |
   | :--- | :--- | :--- | :--- | :--- | :--- |
   | **Left** | 5V | GND | A0 | A1 | D2 |
   | **Right** | 5V | GND | A2 | A3 | D4 |

4. **Important:** Power the servos using an external 5V power supply connected to the PCA9685 terminal block. *Do not power servos directly from the Arduino.*

> Servo cables are usually too short to reach the PCA9685 – extend them by soldering on extra wire.

### 2. Uploading the Arduino Code

1. Open the Arduino IDE.
2. Install the required libraries:
   * **Adafruit PWM Servo Driver Library** – via Library Manager (`Ctrl+Shift+I`), or from the ZIP in `zip-soubory/` (*Sketch → Include Library → Add .ZIP Library*)
   * **LiquidCrystal I2C** – via Library Manager
   * `Wire` and `EEPROM` are built into the Arduino IDE (nothing to install)
3. Open `hotovy_kod.ino`, select your Arduino board and COM port, and click **Upload**.
4. After the upload the LCD shows the servo values `S1`–`S5`.

> **Close the Arduino IDE Serial Monitor** before using the web interface – only one program can use the USB port at a time.

### 3. Web Interface Setup (Python)

Download or clone the repository, open a terminal in the project folder and run:

**Windows**
```bash
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Then open **http://127.0.0.1:5000** in your browser (any modern browser works).

1. Scroll to the **Webové ovládání Arduina** (web control) section.
2. Select the Arduino port from the list (e.g. `COM3` on Windows, `/dev/ttyUSB0` or `/dev/ttyACM0` on Linux, `/dev/cu.usbserial-…` on macOS) and click **Připojit Arduino** (Connect).
3. Set an angle with a slider and confirm with **Odeslat změny** (Send changes), or use the **−5 / +5** buttons for fine adjustment.
4. Use the **Otevřít / Zavřít** buttons for the gripper, **Uložit pozice** to save positions to EEPROM and **Reset na výchozí** to return to the default pose.

> **Try it without hardware:** pick **SIMULACE** in the port list. Nothing is sent to a real device, but you can test the whole interface.

> **Always open the page through `http://127.0.0.1:5000`.** If you open `index.html` directly from disk (or with VS Code Live Server) you will see raw `{{ ... }}` and `{% ... %}` text, because the page is a Flask template that only Python can render.

The server listens on `127.0.0.1` only (your own computer) and has no login, so don't expose it to a network.

---

## Controls Summary

Servo map: **0** gripper · **1** wrist rotation · **2** wrist tilt · **3** forearm · **4** shoulder (main arm) · **5** base.

* **Left Joystick:**
  * **X-Axis:** Forearm (Servo 3)
  * **Y-Axis:** Wrist tilt (Servo 2)
  * **Button (SW1):** Toggle Gripper Open / Closed (Servo 0)
* **Right Joystick:**
  * **X-Axis (Default):** Servo 4
  * **Y-Axis (Default):** Servo 5
  * **Button (SW2):** Toggle wrist mode – the X-axis then controls wrist rotation (Servo 1)
* **Combo Action (SW1 + SW2 pressed together):** Start the automated routine ("Dance mode"). Pressing both buttons again stops it.

---

## Serial Protocol

The web interface only sends plain text lines over USB serial (**9600 baud**, newline-terminated). You can also type these into the Arduino IDE Serial Monitor:

| Command | Description |
| :--- | :--- |
| `<servo> <angle>` | Move a servo, e.g. `3 90` (servo 0–5, angle 0–180) |
| `p` | Save positions to EEPROM |
| `r` | Reset to the default positions |

---

## Configuration

At the top of `app.py` you can change:

* `LIMITS` – allowed angle range for each slider (protects the mechanics of your arm)
* `KLESTE_OTEVRENO` / `KLESTE_ZAVRENO` – gripper angles used by the web buttons (check them on your own arm before using!)
* `VYCHOZI` – default pose (must match `loadPositions()` in `hotovy_kod.ino`)

Look and feel is in `style.css` (colors are at the top in the `:root` block). For automatic reload while editing, run `flask --app app run --debug`.

---

## Troubleshooting

| Problem | Solution |
| :--- | :--- |
| Raw `{{ ... }}` / `{% ... %}` shown on the page | Open **http://127.0.0.1:5000** (started with `python app.py`), not the HTML file directly or Live Server |
| Arduino port is missing in the list | Check the USB cable (it must carry data), install the CH340 driver, reconnect the board and reload the page |
| "could not open port" / "Access denied" | Close the Arduino IDE Serial Monitor and any other program using the port |
| `Permission denied` on Linux | Add yourself to the serial group: `sudo usermod -a -G dialout $USER`, then log out and in again |
| Arduino restarts when connecting | Normal – opening the serial port resets most Arduino boards; the server waits 2 s for it |
| `ModuleNotFoundError: flask` / `serial` | Activate the virtual environment and run `pip install -r requirements.txt` |
| LCD shows nothing | Check the I2C address (`0x27`; some displays use `0x3F`) and the contrast potentiometer on the back of the I2C adapter |
| Servos jitter or the Arduino resets | The servos need their own 5V supply with enough current (MG996R can draw over 1 A each under load) |

---

## Project Structure

```text
├── app.py              # Python (Flask) server + serial communication with the Arduino
├── index.html          # Web dashboard (Flask template)
├── galerie.html        # Photo gallery
├── style.css           # Styling for both pages
├── hotovy_kod.ino      # Arduino firmware
├── requirements.txt    # Python dependencies (Flask, pyserial)
├── foto/               # Photos for the gallery
└── zip-soubory/        # Downloads: PCA9685 library, CH340 driver, STL files of the controller
```

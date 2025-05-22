# B.O.T.A.N.I - Beobachtender Organischer Topf mit Automatischer Navigation und Intelligenz

A smart robotic system for remote plant care, navigation, and monitoring, designed using Raspberry Pis, sensors, and a LEGO vehicle base. B.O.T.A.N.I allows users to drive a plant-bearing vehicle via a custom-built controller equipped with a joystick, LED indicators, a buzzer, and a live video feed.

## Project Structure

```
.
├── RaspberryPi3        # Controller hardware: joystick, display, buzzer, LED
│   ├── view_stream.py
│   ├── joystick.py
│   ├── ledcontrol.py
│   └── requirements.txt
├── RaspberryPi4        # Vehicle logic: motors, camera, distance control
│   ├── camera.py
│   ├── motorsteerdistance.py
│   └── requirements.txt
├── RaspberryPiZero     # Sensor node: brightness, temperature, humidity, distance
│   ├── sensors.py
│   └── requirements.txt
├── Dashboard.html      # Web dashboard for live feed and sensor data
├── README.md
└── ProjectReport.pdf   # Full project report
```

## System Overview

B.O.T.A.N.I consists of three main components:

1. **Controller** - A Raspberry Pi 3 with:

   * A PiTFT screen for live video.
   * Joystick for manual control.
   * RGB LED for temperature indication.
   * Buzzer for soil humidity alerts.

2. **Car Platform** - A LEGO-based vehicle powered by Raspberry Pi 4:

   * Servo motors for movement and steering.
   * Time-of-Flight sensor for collision avoidance.
   * Camera for live video stream.

3. **Sensor Node** - Raspberry Pi Zero:

   * Monitors light, temperature, humidity, and distance.
   * Publishes data via MQTT to the controller and web dashboard.

## How to set up the project

To configure all raspberry PIs, this repository needs to be cloned onto each one of them.
This repo contains folders that correspond to the code that needs to run on each one of the PIs.

### 1. Raspberry Pi 3 - Controller

**Dependencies:**

```bash
cd RaspberryPi3
python3 -m venv .venv --system-site-packages
source .venv/bin/activate
pip install -r requirements.txt
```

**Joystick Setup:**

```bash
sudo raspi-config  # Enable I2C
sudo apt install -y i2c-tools
i2cdetect -y 1     # Should detect ADC at 0x48
```

**Configure PiTFT Display:**

```bash
# Install display driver
sudo apt-get update
sudo apt-get install -y git python3-pip
pip3 install --upgrade adafruit-python-shell click
git clone https://github.com/adafruit/Raspberry-Pi-Installer-Scripts.git
cd Raspberry-Pi-Installer-Scripts

sudo -E env PATH=$PATH python3 adafruit-pitft.py --display=28r --rotation=90 --install-type=console

sudo reboot

# Configure rotation if necessary
# (look for line with the tft screen listed)
vim /boot/firmware/config.txt
sudo reboot
```

**Start All Scripts:**

```bash
python3 joystick.py & python3 ledcontrol.py & python3 view_stream.py
```

### 2. Raspberry Pi 4 - Car System

**Dependencies:**

```bash
cd RaspberryPi4
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Run:**

* `camera.py` for streaming video to `http://<car-ip>:8080/`
* `motorsteerdistance.py` to handle drive + safety logic

```bash
python3 camera.py & python3 motorsteerdistance.py
```

### 3. Raspberry Pi Zero - Sensors

**Dependencies:**

```bash
cd RaspberryPiZero
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Run:**

```bash
python3 sensors.py
```

### 4. Dashboard

Open `Dashboard.html` in a somewhat modern browser.
This file is standalone and does not require to be served by a webserver.
Make sure MQTT broker is accessible at `ws://<rpi4-ip>:8081`.

## Communication Overview

### MQTT Topics

| Topic         | Publisher         | Subscriber(s)                  | Purpose                 |
| ------------- | ----------------- | ------------------------------ | ----------------------- |
| `Brightness`  | Raspberry Pi Zero | Pi 3 (LED), Dashboard          | Plant light level       |
| `Temperature` | Raspberry Pi Zero | Pi 3 (RGB LED), Dashboard      | Ambient temperature     |
| `Humidity`    | Raspberry Pi Zero | Pi 3 (Piezo buzzer), Dashboard | Soil moisture           |
| `Distance`    | Raspberry Pi Zero | Pi 4 (Safety), Dashboard       | Obstacle distance       |
| `joystick/xy` | Raspberry Pi 3    | Pi 4 (motor control)           | Drive/steering commands |

### Video Stream

* The MJPEG stream is accessible at `http://<car-ip>:8080/`

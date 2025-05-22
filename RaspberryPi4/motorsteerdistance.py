import json
import signal
import sys
import time
import threading

import paho.mqtt.client as mqtt
from adafruit_servokit import ServoKit

MQTT_BROKER      = "localhost"
MQTT_PORT        = 1883
JOYSTICK_TOPIC   = "joystick/xy"
DISTANCE_TOPIC   = "Distance"

STEER_SERVO_CH       = 13
DRIVE_SERVO_CH       = 15
DEAD_ZONE            = 0.05
STEER_SPEED          = 0.09
STEER_TRAVEL_TIME_L  = 0.9
STEER_TRAVEL_TIME_R  = 1.0
LOOP_INTERVAL        = 0.02
RECONNECT_DELAY      = 5

kit = ServoKit(channels=16)

_current_x = 0.0
_target_x  = 0.0
_distance  = 255
_lock      = threading.Lock()
_running   = True

def clamp(v, lo=-1.0, hi=1.0):
    return max(lo, min(hi, v))

def on_connect(client, _userdata, _flags, rc):
    client.subscribe(JOYSTICK_TOPIC)
    client.subscribe(DISTANCE_TOPIC)

def on_disconnect(client, _userdata, rc):
    while _running:
        try:
            client.reconnect()
            return
        except Exception:
            time.sleep(RECONNECT_DELAY)

def on_message(client, _userdata, msg):
    global _target_x, _distance

    topic = msg.topic
    payload = msg.payload.decode().strip()

    if topic == DISTANCE_TOPIC:
        try:
            d = float(payload)
            if 0.00 <= d <= 255.00:
                _distance = d
        except ValueError:
            pass
        return

    if topic == JOYSTICK_TOPIC:
        try:
            if payload.startswith("{"):
                data = json.loads(payload)
                x, y = float(data["x"]), float(data["y"])
            else:
                x_str, y_str = payload.split(",", 1)
                x, y = float(x_str), float(y_str)

            x = 0.0 if abs(x) < DEAD_ZONE else clamp(x)
            y = 0.0 if abs(y) < DEAD_ZONE else clamp(y)

            raw_throttle = -y

            if _distance < 100 and raw_throttle > 0:
                raw_throttle = 0.0

            kit.continuous_servo[DRIVE_SERVO_CH].throttle = raw_throttle

            with _lock:
                _target_x = x

        except Exception:
            pass

def steering_loop():
    global _current_x, _running

    while _running:
        with _lock:
            target = _target_x
            current = _current_x

        dx = target - current
        if abs(dx) < 1e-3:
            kit.continuous_servo[STEER_SERVO_CH].throttle = 0.0
        else:
            direction = 1.0 if dx > 0 else -1.0
            units_per_sec = 1.0 / (STEER_TRAVEL_TIME_R if direction > 0 else STEER_TRAVEL_TIME_L)
            kit.continuous_servo[STEER_SERVO_CH].throttle = STEER_SPEED * direction
            delta = direction * units_per_sec * LOOP_INTERVAL
            if abs(delta) >= abs(dx):
                _current_x = target
                kit.continuous_servo[STEER_SERVO_CH].throttle = 0.0
            else:
                _current_x = current + delta

        time.sleep(LOOP_INTERVAL)

def shutdown(_sig=None, _frame=None):
    global _running
    _running = False
    time.sleep(LOOP_INTERVAL * 2)
    kit.continuous_servo[STEER_SERVO_CH].throttle = 0.0
    kit.continuous_servo[DRIVE_SERVO_CH].throttle  = 0.0
    client.loop_stop()
    sys.exit(0)

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

threading.Thread(target=steering_loop, daemon=True).start()

client = mqtt.Client()
client.on_connect    = on_connect
client.on_disconnect = on_disconnect
client.on_message    = on_message

while True:
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        break
    except Exception:
        time.sleep(RECONNECT_DELAY)

client.loop_start()

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    shutdown()

import threading
import time
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
from gpiozero import PWMLED, DigitalOutputDevice

LED_BRIGHT_PIN = 22
LED_R_PIN      = 4
LED_G_PIN      = 17
LED_B_PIN      = 27
BUZZER_PIN     = 23
BUTTON_PIN     = 14   
BUTTON2_PIN    = 15   

LUX_MIN   = 0
LUX_MAX   = 1000
TEMP_COLD = 15
TEMP_HOT  = 28

led_brightness = PWMLED(LED_BRIGHT_PIN)
led_red        = PWMLED(LED_R_PIN)
led_green      = PWMLED(LED_G_PIN)
led_blue       = PWMLED(LED_B_PIN)
buzzer         = DigitalOutputDevice(BUZZER_PIN)

GPIO.setmode(GPIO.BCM)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(BUTTON2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

buzzer_blinking = False
disable_buzzer  = False

def _button_poller():
    global disable_buzzer, buzzer_blinking
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            disable_buzzer   = True
            buzzer.off()
            buzzer_blinking  = False
            while GPIO.input(BUTTON_PIN) == GPIO.LOW:
                time.sleep(0.05)
        time.sleep(0.05)

threading.Thread(target=_button_poller, daemon=True).start()

def scale_lux_to_pwm(lux):
    lux = max(LUX_MIN, min(lux, LUX_MAX))
    return lux / LUX_MAX

def temperature_to_rgb(temp):
    if temp <= TEMP_COLD:
        return (0.0, 0.0, 1.0)
    if temp >= TEMP_HOT:
        return (1.0, 0.0, 0.0)
    if temp < 22:
        ratio = (temp - TEMP_COLD) / (22 - TEMP_COLD)
        return (0.0, ratio, 1.0 - ratio)
    ratio = (temp - 22) / (TEMP_HOT - 22)
    return (ratio, 1.0 - ratio, 0.0)

def set_rgb(r, g, b):
    led_red.value   = r
    led_green.value = g
    led_blue.value  = b

def on_message(client, userdata, msg):
    global buzzer_blinking, disable_buzzer
    topic = msg.topic

    try:
        value = float(msg.payload.decode())
    except ValueError:
        return

    if topic == MQTT_TOPIC_BRIGHT:
        led_brightness.value = scale_lux_to_pwm(value)
    elif topic == MQTT_TOPIC_TEMP:
        set_rgb(*temperature_to_rgb(value))
    elif topic == MQTT_TOPIC_HUMID:
        if value < 50:
            if not disable_buzzer and not buzzer_blinking:
                buzzer.blink(on_time=0.5, off_time=0.5)
                buzzer_blinking = True
        else:
            disable_buzzer = False
            if buzzer_blinking:
                buzzer.off()
                buzzer_blinking = False

MQTT_BROKER        = "rpi4"
MQTT_TOPIC_BRIGHT = "Brightness"
MQTT_TOPIC_TEMP   = "Temperature"
MQTT_TOPIC_HUMID  = "Humidity"

def on_disconnect(client, userdata, rc):
    if rc != 0:
        reconnect()

client = mqtt.Client()
client.on_message = on_message
client.on_disconnect = on_disconnect

def reconnect():
    while True:
        try:
            client.connect(MQTT_BROKER, 1883, 5)
            client.subscribe([
                (MQTT_TOPIC_BRIGHT, 0),
                (MQTT_TOPIC_TEMP,   0),
                (MQTT_TOPIC_HUMID,  0),
            ])
            break
        except Exception:
            time.sleep(5)

reconnect()

try:
    client.loop_forever()
except KeyboardInterrupt:
    pass
finally:
    led_brightness.off()
    set_rgb(0, 0, 0)
    buzzer.off()
    GPIO.cleanup()
    client.disconnect()

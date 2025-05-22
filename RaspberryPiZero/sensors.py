import time
import math
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import paho.mqtt.client as mqtt
import adafruit_vl6180x

I2C_ADDRESS = 0x48
DIVIDER_VCC = 3.3
R_FIXED = 10_000.0

L1, R1 = 1.0, 80e3
L2, R2 = 100.0, 1.5e3

b = math.log10(R2 / R1) / math.log10(L2 / L1)
a = R1 / (L1 ** b)

MQTT_BROKER = "rpi4"
MQTT_PORT = 1883
MQTT_TOPIC_BRIGHT = "Brightness"
MQTT_TOPIC_TEMP = "Temperature"
MQTT_TOPIC_HUM = "Humidity"
MQTT_TOPIC_TOF = "Distance"

def voltage_to_resistance(v_out, vcc=DIVIDER_VCC, r_fixed=R_FIXED):
    if v_out <= 0 or v_out >= vcc:
        return float('inf')
    return r_fixed * (vcc / v_out - 1.0)

def resistance_to_lux(R):
    return (R / a) ** (1.0 / b)

def voltage_to_temp(U):
    return U * 100 - 50

def voltage_to_hum(U):
    return min(100.0, max(0.0, (3.3 - U) / 2.3 * 100.0))

def main():
    i2c = busio.I2C(board.SCL, board.SDA)
    tof = adafruit_vl6180x.VL6180X(i2c)
    ads = ADS.ADS1115(i2c, address=I2C_ADDRESS)
    ldr_chan = AnalogIn(ads, ADS.P0)
    temp_chan = AnalogIn(ads, ADS.P1)
    hum_chan = AnalogIn(ads, ADS.P2)

    client = mqtt.Client()
    connected = False

    def on_connect(client, userdata, flags, rc):
        nonlocal connected
        if rc == 0:
            connected = True

    def on_disconnect(client, userdata, rc):
        nonlocal connected
        connected = False

    client.on_connect = on_connect
    client.on_disconnect = on_disconnect

    while not connected:
        try:
            client.connect(MQTT_BROKER, MQTT_PORT, keepalive=5)
            client.loop_start()
            time.sleep(1)
        except Exception:
            time.sleep(5)

    try:
        while True:
            if not connected:
                while not connected:
                    try:
                        client.reconnect()
                        time.sleep(1)
                    except Exception:
                        time.sleep(5)

            v0 = ldr_chan.voltage
            R_ldr = voltage_to_resistance(v0)
            lux = resistance_to_lux(R_ldr)

            v1 = temp_chan.voltage
            temp = voltage_to_temp(v1)

            v2 = hum_chan.voltage
            hum = voltage_to_hum(v2)

            distance = tof.range

            try:
                client.publish(MQTT_TOPIC_BRIGHT, f"{lux:.2f}")
                client.publish(MQTT_TOPIC_TEMP, f"{temp:.2f}")
                client.publish(MQTT_TOPIC_HUM, f"{hum:.2f}")
                client.publish(MQTT_TOPIC_TOF, f"{distance:.2f}")
            except Exception:
                continue

            time.sleep(0.1)

    except KeyboardInterrupt:
        pass
    finally:
        client.loop_stop()
        client.disconnect()

if __name__ == "__main__":
    main()

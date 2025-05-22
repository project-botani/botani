import board
import busio
import time
import paho.mqtt.publish as publish
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
chan_x = AnalogIn(ads, ADS.P0)
chan_y = AnalogIn(ads, ADS.P1)

minx = 3461
maxx = 21160
miny = 3207
maxy = 20522

threshx = 0.06
threshy = 0.11

def get_xy():
    x = ((chan_x.value - minx) / (maxx - minx)) * 2 - 1
    y = ((chan_y.value - miny) / (maxy - miny)) * 2 - 1

    x = 0 if abs(x) < threshx else x
    y = 0 if abs(y) < threshy else y

    return x, y

while True:
    x, y = get_xy()
    try:
        publish.single(
            "joystick/xy",
            f"{x:.3f},{y:.3f}",
            hostname="192.168.31.178",
            port=1883
        )
    except:
        pass
    time.sleep(0.05)

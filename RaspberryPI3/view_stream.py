import cv2
import os
import time

WIDTH = 320
HEIGHT = 240
FB_DEVICE = "/dev/fb1"
STREAM_URL = 'http://192.168.31.178:8080/?action=stream'

def open_stream():
    cap = cv2.VideoCapture(STREAM_URL, cv2.CAP_FFMPEG)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap

fb = open(FB_DEVICE, "wb")
cap = open_stream()

while True:
    ret, frame = cap.read()
    if not ret or frame is None:
        cap.release()
        time.sleep(1)
        cap = open_stream()
        continue

    frame = cv2.resize(frame, (WIDTH, HEIGHT))
    frame_4c = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)

    fb.seek(0)
    fb.write(frame_4c.tobytes())
    fb.flush()

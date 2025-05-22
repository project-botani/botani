from picamera2 import Picamera2
from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
import cv2
import uvicorn
import threading
import time
import io

app = FastAPI()

picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (320, 240)})
picam2.configure(config)
picam2.start()

latest_frame = {"data": None}
frame_lock = threading.Lock()

def capture_frames():
    while True:
        buffer = io.BytesIO()
        frame = picam2.capture_array()
        frame = cv2.flip(frame, 0)
        frame = cv2.flip(frame, 1)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        success, jpg = cv2.imencode(".jpg", frame)
        if success:
            with frame_lock:
                latest_frame["data"] = jpg.tobytes()
        time.sleep(0.03)

threading.Thread(target=capture_frames, daemon=True).start()

@app.get("/")
def video_feed():
    def mjpeg_stream():
        while True:
            with frame_lock:
                frame = latest_frame["data"]
            if frame:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
            time.sleep(0.03)
    return StreamingResponse(mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)

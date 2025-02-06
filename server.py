import uvicorn
import time
import numpy as np
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from picamera2 import Picamera2
import cv2

app = FastAPI()
templates = Jinja2Templates(directory="templates")

class VideoCamera:
    def __init__(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_video_configuration(main={"size": (1920, 1080)})
        self.picam2.configure(config)
        self.picam2.start()

    def __del__(self):
        self.picam2.stop()

    def get_frame(self):
        image = self.picam2.capture_array()
        image = cv2.resize(image, (640, 360))  # Resize for streaming
        ret, jpeg = cv2.imencode('.jpg', image)
        if not ret:
            raise RuntimeError("Could not encode frame as JPEG")
        return jpeg.tobytes()

@app.get('/')
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

def gen(camera):
    count = 1
    start_time = time.time()
    while True:
        start_frame_time = time.time()

        if count % 20 == 0:
            end_time = time.time()
            fps_avg = 20 / (end_time - start_time)
            print(f"FPS Promedio: {fps_avg:.6f}")
            start_time = end_time

        frame_bytes = camera.get_frame()
        yield (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n\r\n')

        end_frame_time = time.time()
        fps_frame = 1 / (end_frame_time - start_frame_time)
        print(f"FPS Frame: {fps_frame:.6f}")

        count += 1

@app.get('/video_feed')
def video_feed():
    return StreamingResponse(gen(VideoCamera()), media_type="multipart/x-mixed-replace;boundary=frame")

if __name__ == '__main__':
    uvicorn.run("server:app", host="0.0.0.0", port=5000, access_log=False)


from flask import Flask, Response
import cv2
from ultralytics import YOLO
import numpy as np

# Load YOLO model
def load_model(model_path):

    model = YOLO(model_path)  # Ganti dengan path model YOLO Anda
    return model

# Fungsi untuk streaming video
def video_feed(CCTV_IP, model):
    camera_source = f"{CCTV_IP}/video"  # Ganti dengan URL atau IP CCTV Anda
    
    # Buka koneksi ke CCTV
    cap = cv2.VideoCapture(camera_source)
    
    if not cap.isOpened():
        return "Error: Unable to access the camera."

    def generate():
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Deteksi objek pada frame menggunakan model YOLO
            results = model(frame)  # Deteksi objek pada frame

            # Ambil kotak deteksi dan gambar hasil deteksi
            for result in results:
                boxes = result.boxes  # Ambil kotak deteksi
                for box in boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0].item()
                    label = result.names[box.cls[0].item()]
                    
                    # Gambar kotak deteksi pada frame
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            # Encode frame ke dalam format JPEG
            _, jpeg = cv2.imencode('.jpg', frame)
            if not _:
                continue

            # Kirim frame sebagai response dalam format multipart JPEG
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')




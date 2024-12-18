import cv2
import numpy as np
from ultralytics import YOLO
from dotenv import load_dotenv
import os
from supabase import create_client, Client
from datetime import datetime
import uuid
from io import BytesIO
from app.helpers.logger import setup_logger
from app import create_app
from app.controllers.detection_controller import get_owner_id_by_cctv_ip
from app.controllers.detection_controller import create_report

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CCTV_IP = os.getenv("CCTV_IP")

app = create_app()
logger = setup_logger("detection")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
is_detection_active = True

def save_detection_images(owner_id, image, label=""):
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        unique_id = str(uuid.uuid4())
        filename = f"{label}_{unique_id}.jpg"

        _, buffer = cv2.imencode('.jpg', image)
        file_bytes = BytesIO(buffer)

        supabase_path = f"{owner_id}/{timestamp}/{timestamp}_{filename}"
        supabase.storage.from_("foto-maling").upload(supabase_path, file_bytes.getvalue())
        public_url = supabase.storage.from_("foto-maling").get_public_url(supabase_path)

        return public_url
    except Exception as e:
        print(f"Error saving or uploading image: {e}")
        return None

def load_model(model_path):
    try:
        # Load YOLO model
        model = YOLO(model_path, task='detect')
        logger.info(f"Model loaded successfully. Available classes: {model.names}")
        return model
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise

def process_frame(frame, model):
    try:
        results = model(frame, conf=0.35)  # Increased confidence threshold
        
        # Add logging for debugging
        if results and results[0].boxes:
            for box in results[0].boxes:
                conf = float(box.conf)
                class_id = int(box.cls)
                class_name = results[0].names[class_id]
                logger.debug(f"Detection: {class_name} with confidence {conf:.2f}")
        
        return results[0] if results else None
    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        return None

def draw_detections(frame, results, owner_id):
    images_captured = []
    
    if results and hasattr(results, 'boxes'):
        for box in results.boxes:
            conf = float(box.conf)
            class_id = int(box.cls)
            class_name = results.names[class_id]
            
            # Additional validation for knife detection
            is_valid_detection = False
            if conf >= 0.8:  # Increased confidence threshold
                # Additional checks for knife detection
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detection_width = x2 - x1
                detection_height = y2 - y1
                aspect_ratio = detection_width / detection_height if detection_height != 0 else 0
                
                # Typical knife aspect ratio and size checks
                if detection_width > 20 and detection_height > 20:
                    is_valid_detection = True
            
            if is_valid_detection:
                # Different colors for different classes
                color = (0, 0, 255)  # Red for knife
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                label = f"{class_name}: {conf:.2f}"
                cv2.putText(frame, label, (x1, y1 - 10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                
                # Additional logging
                logger.info(f"Valid knife detection - Confidence: {conf:.2f}, " 
                          f"Aspect Ratio: {aspect_ratio:.2f}, "
                          f"Size: {detection_width}x{detection_height}")
                
                # Save detection image only for valid detections
                image_url = save_detection_images(owner_id, frame, label=class_name.lower())
                if image_url:
                    images_captured.append(image_url)
                    logger.info(f"Saved knife detection image with confidence {conf:.2f}")

    return frame, images_captured

def real_time_detection(model_path, camera_source):
    logger.info("detection,Starting real-time detection...")
    camera_source = f"{CCTV_IP}/video"
    
    with app.app_context():
        logger.info(f"Getting owner ID for CCTV IP: {CCTV_IP}")
        owner_id = get_owner_id_by_cctv_ip(CCTV_IP)
        
        if not owner_id:
            logger.error("Owner ID not found for the provided CCTV IP")
            return

    global is_detection_active
    
    model = load_model(model_path)

    cap = cv2.VideoCapture(camera_source)
    
    if not cap.isOpened():
        logger.error("Unable to open video source.")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 60)
    all_images_captured = []

    try:
        while is_detection_active:
            ret, frame = cap.read()
            if not ret:
                logger.error("Failed to read frame from camera.")
                break

            # Process the frame
            results = process_frame(frame, model)
            if results is not None:
                # Detect and draw results
                frame, images_captured = draw_detections(frame, results, owner_id)
                print(images_captured)
                # Add captured images to the list
                for image_url in images_captured:
                    if len(all_images_captured) < 1:
                        all_images_captured.append(image_url)
                        logger.info(f"Image URL added: {image_url}")
                    else:
                        break
    

                # Stop detection after 2 images
                if len(all_images_captured) == 1:
                    logger.info("2 images captured. Creating report...")
                    with app.app_context():
                        create_report(owner_id, all_images_captured[:1], "Detection report generated.")
                    logger.info("Report created successfully.")
                    is_detection_active = False  # Stop detection
                    break
                

            # Optional: press 'q' to quit
            if cv2.waitKey(1) & 0xFF == ord('q'):
                logger.info("Detection stopped manually by user.")
                break

    except Exception as e:
        logger.error(f"Error during detection: {e}")
        print(f"Error during detection: {e}")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        is_detection_active = False
        logger.info("Detection stopped, resources released.")

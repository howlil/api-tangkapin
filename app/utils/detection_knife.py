import cv2
from flask import jsonify
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
import threading
import time

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
CCTV_IP = os.getenv("CCTV_IP")

app = create_app()
logger = setup_logger("detection")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
is_detection_active = True

# Create temp directory for local storage
os.makedirs("temp_detections", exist_ok=True)

# Create queues for image processing
from queue import Queue
image_save_queue = Queue()
image_url_queue = Queue()

def save_detection_images_worker():
    """Worker thread function to save images asynchronously"""
    while is_detection_active or not image_save_queue.empty():
        try:
            if not image_save_queue.empty():
                owner_id, image, label = image_save_queue.get()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M")
                unique_id = str(uuid.uuid4())
                filename = f"{label}_{unique_id}.jpg"
                
                # First save locally as a fallback
                local_dir = os.path.join("temp_detections", str(owner_id), timestamp)
                os.makedirs(local_dir, exist_ok=True)
                local_path = os.path.join(local_dir, filename)
                cv2.imwrite(local_path, image)
                
                # Try Supabase upload
                try:
                    _, buffer = cv2.imencode('.jpg', image)
                    file_bytes = BytesIO(buffer)
                    
                    supabase_path = f"{owner_id}/{timestamp}/{timestamp}_{filename}"
                    supabase.storage.from_("foto-maling").upload(supabase_path, file_bytes.getvalue())
                    public_url = supabase.storage.from_("foto-maling").get_public_url(supabase_path)
                    
                    # Return the Supabase URL
                    image_url_queue.put(public_url)
                    logger.info(f"Image uploaded to Supabase: {public_url}")
                except Exception as e:
                    # If Supabase fails, use local file path
                    logger.warning(f"Supabase upload failed: {e}")
                    file_url = f"file://{os.path.abspath(local_path)}"
                    image_url_queue.put(file_url)
                    logger.info(f"Using local file instead: {file_url}")
            else:
                # Sleep to prevent CPU spinning
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"Error in image save worker: {e}")
        finally:
            if not image_save_queue.empty():
                image_save_queue.task_done()

def save_detection_images(owner_id, image, label=""):
    """Add an image to the save queue and return immediately"""
    image_save_queue.put((owner_id, image.copy(), label))
    return "pending_upload"  # Return placeholder

def load_model(model_path):
    try:
        # Load YOLO model
        model = YOLO(model_path, task='detect')
        logger.info(f"Model loaded successfully")
        return model
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise

def process_frame(frame, model):
    try:
        # Resize frame to speed up processing - 50% reduction
        frame_height, frame_width = frame.shape[:2]
        resize_factor = 0.5
        small_frame = cv2.resize(frame, (int(frame_width * resize_factor), int(frame_height * resize_factor)))
        
        # First-pass detection on smaller frame
        results = model(small_frame, conf=0.5)
        
        # If anything detected in small frame, verify on full frame
        if results and len(results[0].boxes) > 0:
            # Process the full frame for better accuracy
            results = model(frame, conf=0.35)
            return results[0] if results else None
        return None
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
            
            # Validate detection
            if conf >= 0.7:  # Reduced from 0.8 for better detection rate
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detection_width = x2 - x1
                detection_height = y2 - y1
                
                # Simplified validation
                if detection_width > 20 and detection_height > 20:
                    # Draw on frame
                    color = (0, 0, 255)  # Red for knife
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    label = f"{class_name}: {conf:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10), 
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    
                    # Add to queue for saving
                    image_url = save_detection_images(owner_id, frame, label=class_name.lower())
                    if image_url:
                        images_captured.append(image_url)
                        logger.info(f"Image queued for saving: {image_url}")

    return frame, images_captured

def real_time_detection(model_path, camera_source):
    logger.info("Starting real-time detection...")
    camera_source = f"{CCTV_IP}/video"
    
    with app.app_context():
        logger.info(f"Getting owner ID for CCTV IP: {CCTV_IP}")
        owner_id = get_owner_id_by_cctv_ip(CCTV_IP)
        
        if not owner_id:
            logger.error("Owner ID not found for the provided CCTV IP")
            return

    global is_detection_active
    is_detection_active = True
    
    # Start worker thread for image saving
    save_thread = threading.Thread(target=save_detection_images_worker)
    save_thread.daemon = True
    save_thread.start()
    
    model = load_model(model_path)

    cap = cv2.VideoCapture(camera_source)
    
    if not cap.isOpened():
        logger.error("Unable to open video source.")
        return
    
    # Set lower resolution and frame rate
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 15)  # Reduced from 60 to 15 FPS
    
    all_images_captured = []
    frame_counter = 0
    last_motion_frame = None
    detection_start_time = time.time()
    
    # Max detection time in seconds
    max_detection_time = 60
    
    try:
        while is_detection_active:
            # Check if we've been running too long without a detection
            current_time = time.time()
            if current_time - detection_start_time > max_detection_time:
                logger.info(f"Detection timeout after {max_detection_time} seconds")
                break
            
            ret, frame = cap.read()
            if not ret:
                logger.error("Failed to read frame from camera.")
                break

            # Frame skipping - only process every 4th frame
            frame_counter += 1
            if frame_counter % 4 != 0:
                continue
            
            # Simple motion detection
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)
            
            if last_motion_frame is not None:
                frame_delta = cv2.absdiff(last_motion_frame, gray_frame)
                thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
                motion_detected = np.sum(thresh) > 5000  # Higher threshold for motion
                
                # Skip processing if no motion detected
                if not motion_detected:
                    last_motion_frame = gray_frame
                    continue
            
            last_motion_frame = gray_frame

            # Process the frame
            results = process_frame(frame, model)
            if results is not None:
                # Detect and draw results
                frame, images_captured = draw_detections(frame, results, owner_id)
                
                # Check for completed uploads
                while not image_url_queue.empty():
                    image_url = image_url_queue.get()
                    if len(all_images_captured) < 1:
                        all_images_captured.append(image_url)
                        logger.info(f"Image URL added: {image_url}")
                    
                # Create report after capturing image
                if len(all_images_captured) == 1:
                    logger.info("Image captured. Creating report...")
                    with app.app_context():
                        # Handle local file URLs
                        urls_for_report = []
                        for url in all_images_captured:
                            if url.startswith("file://"):
                                # If this is a local file, we might need to copy it to a web-accessible location
                                # For now, we'll just use it directly
                                urls_for_report.append(url)
                            else:
                                urls_for_report.append(url)
                        
                        create_report(owner_id, urls_for_report, "Detection report generated.")
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
        # Wait for image saving to complete
        if not image_save_queue.empty():
            logger.info("Waiting for image saving to complete...")
            image_save_queue.join()
        
        cap.release()
        cv2.destroyAllWindows()
        is_detection_active = False
        logger.info("Detection stopped, resources released.")


# Updated version of create_report to handle local file URLs
def modified_create_report(owner_id, array_image, description):
    """Modified create_report function that can handle local file paths"""
    try:
        # This would be inserted into the controllers/detection_controller.py
        # to handle local file URLs in the report creation process
        
        logger.info("Starting to create modified report...")
        
        if not owner_id or not array_image or not description:
            logger.error("Invalid input: Missing required fields.")
            return jsonify({"error": "Invalid input, all fields are required"}), 400
        
        # Check if array_image contains local file URLs
        processed_images = []
        for image_url in array_image:
            if image_url.startswith("file://"):
                # For local files, extract the local path
                local_path = image_url[7:]  # Remove 'file://' prefix
                
                # Read the image and create a base64 representation
                with open(local_path, "rb") as img_file:
                    img_data = img_file.read()
                    
                # For handling in your frontend, you could create a data URL
                # or store the file somewhere accessible via HTTP
                
                # For simplicity, we'll just use the path
                processed_images.append(image_url)
            else:
                processed_images.append(image_url)
                
        # Continue with existing create_report logic but using processed_images
        # ...
        
    except Exception as e:
        logger.error(f"Error in modified create_report: {e}")
        # Handle the error appropriately
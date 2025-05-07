from app import create_app
import os
from dotenv import load_dotenv
from app.utils.detection_knife import real_time_detection
from app.helpers.logger import setup_logger
import threading

logger = setup_logger("App")
app = create_app()
load_dotenv()

MODELS = "app/models/best.pt"
CCTV_IP = os.getenv("CCTV_IP")


def start_real_time_detection():
    """
    Start real-time detection as a background process.
    """
    try:
        logger.info("run.py ,Starting real-time detection...")
        real_time_detection(MODELS, CCTV_IP)
    except Exception as e:
        logger.error(f"Error in real-time detection: {e}")



if __name__ == "__main__":
    # Thread untuk real-time detection
    detection_thread = threading.Thread(target=start_real_time_detection, daemon=True)
    detection_thread.start()


    logger.info("Starting Flask server...")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=True)

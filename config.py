import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_ALGORITHM = "HS256"

    # Environment
    FLASK_ENV = os.getenv("NODE_ENV", "development")  # Default: development
    DEBUG = FLASK_ENV == "development"

    # CORS (Cross-Origin Resource Sharing)
    CORS_HEADERS = "Content-Type"

    # Kafka Configuration (if needed)
    KAFKA_BROKER = os.getenv("KAFKA_BROKER")
    TOPIC_NAME = os.getenv("TOPIC_NAME")

    # Application Port
    PORT = int(os.getenv("PORT", 8080))

    # Logging
    LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

    # Database Connection Pool (Optional for large apps)
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_size": 10,
        "pool_timeout": 30,
        "max_overflow": 20,
    }

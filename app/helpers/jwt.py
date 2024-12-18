import jwt
from datetime import datetime, timedelta
from config import Config

def create_jwt_token(user_id, role):
    payload = {
        "id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)  
    }
    token = jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)
    return token

def decode_jwt_token(token):
    try:
        decoded = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        return decoded
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")

from flask import request, jsonify
from functools import wraps
from app.helpers.jwt import decode_jwt_token

def authenticate(f):
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')

            if not auth_header:
                raise ValueError("Authorization token is missing.")

            if not auth_header.startswith("Bearer "):
                raise ValueError("Invalid Authorization header format. Use 'Bearer <token>'.")
            token = auth_header.split(" ")[1]
            decoded = decode_jwt_token(token)
            request.user = decoded
            return f(*args, **kwargs)

        except ValueError as e:
            return jsonify({
                "error": True,
                "message": str(e),
                "data": None
            }), 401
        except Exception as e:
            return jsonify({
                "error": True,
                "message": "An unexpected error occurred during authentication.",
                "data": {"details": str(e)}  # Jangan tampilkan detail error di production
            }), 500

    return decorated_function


def authorize(required_role):

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                user = getattr(request, 'user', None)
                if not user:
                    raise ValueError("User not authenticated. Please provide a valid token.")

                if user.get("role") != required_role:
                    raise ValueError(f"Access forbidden. Role '{required_role}' is required.")

                return f(*args, **kwargs)

            except ValueError as e:
                return jsonify({
                    "error": True,
                    "message": str(e),
                    "data": None
                }), 403
            except Exception as e:
                return jsonify({
                    "error": True,
                    "message": "An unexpected error occurred during authorization.",
                    "data": {"details": str(e)}  
                }), 500

        return decorated_function
    return decorator

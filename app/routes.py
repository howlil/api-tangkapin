from flask import Blueprint, request, jsonify
from app.controllers.auth_controller import login_user
from app.middlewares.auth_middleware import authenticate, authorize
from app.controllers.report_controller import get_predicts, get_predict_detail, get_predicts_all, get_predict_detail_police
from app.controllers.cctv_controller import video_feed, load_model
from app.controllers.detection_controller import update_status
import os
from dotenv import load_dotenv

main_bp = Blueprint('main', __name__)


@main_bp.route('/', methods=['GET'])
def home():
    return {
        "message": "API is Ready!",
    }


@main_bp.route('/api/v1/login', methods=['POST'])
def login():
    data = request.get_json()
    return login_user(data)


@main_bp.route('/me', methods=['GET'])
@authenticate 
# @authorize("POLICE")
def protected():
    user = request.user 
    return jsonify({
        "error": False,
        "message": "Access granted.",
        "data": {
            "user_id": user["id"],
            "role": user["role"]
        }
    })
    
@main_bp.route('/api/v1/reports', methods=['GET'])
@authenticate
def get_predict_results():
    return get_predicts()


@main_bp.route('/api/v2/reports', methods=['GET'])
@authenticate
@authorize("POLICE")
def get_predict_results_all():
    return get_predicts_all()

@main_bp.route('/api/v1/reports/<uuid:predict_id>', methods=['GET'])
@authenticate
def get_predict_details(predict_id):
    return get_predict_detail(predict_id)

@main_bp.route('/api/v2/reports/<uuid:predict_id>', methods=['GET'])
@authenticate
@authorize("POLICE")
def get_predict_detail_polices(predict_id):
    return get_predict_detail_police(predict_id)

@main_bp.route('/api/v1/reports/<uuid:predict_id>', methods=['PATCH'])
@authenticate
@authorize("POLICE")
def update_status_predict(predict_id):
    data = request.get_json()
    return update_status(predict_id, data)

@main_bp.route('/api/v1/cctv', methods=['GET'])
# @authenticate
def video_stream():
    CCTV_IP = os.getenv("CCTV_IP")
    model = load_model("app/models/best.pt")  
    return video_feed(CCTV_IP, model)
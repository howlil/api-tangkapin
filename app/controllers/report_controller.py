from flask import jsonify, request
from app.models import Predict, Images, User
from sqlalchemy.orm import joinedload
from sqlalchemy import desc


# Get all predicts for police
def get_predicts_all():
    try:
        results = (Predict.query
                  .options(
                      joinedload(Predict.images),
                      joinedload(Predict.user)
                  )
                  .order_by(Predict.created_at.desc())
                  .all())

        formatted_results = []
        for predict in results:
            predict_data = {
                'id': str(predict.id),
                'status': predict.status.value,
                'created_at': predict.created_at.isoformat(),
                'deskripsi': predict.deskripsi,
                'images': [{
                    'id': str(image.id),
                    'name_image': image.name_image
                } for image in predict.images]
            }
            formatted_results.append(predict_data)

        return jsonify({
            "error": False,
            "message": "Predict results retrieved successfully.",
            "data": formatted_results
        }), 200

    except Exception as e:
        return jsonify({
            "error": True,
            "message": "An error occurred while retrieving predict results.",
            "data": {"details": str(e)}
        }), 500
                

# Get predicts for specific user
def get_predicts():
    try:
        user_id = request.user.get('id')
        if not user_id:
            return jsonify({
                "error": True,
                "message": "User ID not found in token.",
                "data": None
            }), 400

        results = (Predict.query
                  .options(
                      joinedload(Predict.images),
                      joinedload(Predict.user)
                  )
                  .filter(Predict.user_id == user_id)
                  .order_by(Predict.created_at.desc())
                  .all())

        formatted_results = []
        for predict in results:
            predict_data = {
                'id': str(predict.id),
                'status': predict.status.value,
                'created_at': predict.created_at.isoformat(),
                'deskripsi': predict.deskripsi,
                'images': [{
                    'id': str(image.id),
                    'name_image': image.name_image
                } for image in predict.images]
            }
            formatted_results.append(predict_data)

        return jsonify({
            "error": False,
            "message": "Predict results retrieved successfully.",
            "data": formatted_results
        }), 200

    except Exception as e:
        return jsonify({
            "error": True,
            "message": "An error occurred while retrieving predict results.",
            "data": {"details": str(e)}
        }), 500

def get_last_report_time(user_id):
    try:
        # Fetch the latest report's 'created_at' for the user
        latest_report = (
            Predict.query
            .filter(Predict.user_id == user_id)
            .order_by(Predict.created_at.desc())
            .limit(1)
            .one_or_none()  # Returns a single result or None
        )

        # Check if a report exists and return the 'created_at' field
        return latest_report.created_at if latest_report else None

    except Exception as e:
        # Log or handle exceptions (optional)
        print(f"An error occurred: {e}")
        return None


def get_predict_detail(predict_id):
    try:
        user_id = request.user.get('id')
        if not user_id:
            return jsonify({
                "error": True,
                "message": "User ID not found in token.",
                "data": None
            }), 400

        predict = (Predict.query
                 .options(
                     joinedload(Predict.images),
                     joinedload(Predict.user)
                 )
                 .filter(
                     Predict.user_id == user_id,
                     Predict.id == predict_id
                 )
                .first())

        if not predict:
            return jsonify({
                "error": True,
                "message": "Predict result not found.",
                "data": None
            }), 404

        detail_data = {
            'id': str(predict.id),
            'status': predict.status.value,
            'created_at': predict.created_at.isoformat(),
            'updated_at': predict.updated_at.isoformat(),
            'deskripsi': predict.deskripsi,
            'images': [{
                'id': str(image.id),
                'name_image': image.name_image,
                'created_at': image.created_at.isoformat()
            } for image in predict.images],
            'user': {
                'name': predict.user.name,
                'email': predict.user.email,
                'address': predict.user.address,
                'lang': predict.user.lang,
                'lat': predict.user.lat
            }
        }

        return jsonify({
            "error": False,
            "message": "Predict detail retrieved successfully.",
            "data": detail_data
        }), 200

    except Exception as e:
        return jsonify({
            "error": True,
            "message": "An error occurred while retrieving predict detail.",
            "data": {"details": str(e)}
        }), 500
        
        
def get_predict_detail_police(predict_id):
    try:
        predict = (Predict.query
                 .options(
                     joinedload(Predict.images),
                     joinedload(Predict.user)
                 )
                 .filter(
                     Predict.id == predict_id
                 )
                .first())

        if not predict:
            return jsonify({
                "error": True,
                "message": "Predict result not found.",
                "data": None
            }), 404

        detail_data = {
            'id': str(predict.id),
            'status': predict.status.value,
            'created_at': predict.created_at.isoformat(),
            'updated_at': predict.updated_at.isoformat(),
            'deskripsi': predict.deskripsi,
            'images': [{
                'id': str(image.id),
                'name_image': image.name_image,
                'created_at': image.created_at.isoformat()
            } for image in predict.images],
            'user': {
                'name': predict.user.name,
                'email': predict.user.email,
                'address': predict.user.address,
                'lang': predict.user.lang,
                'lat': predict.user.lat
            }
        }

        return jsonify({
            "error": False,
            "message": "Predict detail retrieved successfully.",
            "data": detail_data
        }), 200

    except Exception as e:
        return jsonify({
            "error": True,
            "message": "An error occurred while retrieving predict detail.",
            "data": {"details": str(e)}
        }), 500
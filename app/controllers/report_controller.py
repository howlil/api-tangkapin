from flask import jsonify, request
from app.models import ResultPredict, Predict, Images, User
from sqlalchemy.orm import joinedload
from sqlalchemy import desc


# 
def get_predicts_all():
    try:

        results = (ResultPredict.query
                  .options(
                      joinedload(ResultPredict.predict)
                     .joinedload(Predict.images),
                     joinedload(ResultPredict.user)
                  )
                  .order_by(ResultPredict.created_at.desc())
                  .all())

        formatted_results = []
        for result in results:
            predict_data = {
                'id': str(result.id),
                'status': result.status.value,
                'created_at': result.created_at.isoformat(),
                'predict': {
                    'id': str(result.predict.id),
                    'deskripsi': result.predict.deskripsi,
                    'images': [{
                        'id': str(image.id),
                        'name_image': image.name_image
                    } for image in result.predict.images]
                }
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
                

def get_predicts():
    try:
        user_id = request.user.get('id')
        if not user_id:
            return jsonify({
                "error": True,
                "message": "User ID not found in token.",
                "data": None
            }), 400

        results = (ResultPredict.query
                  .options(
                      joinedload(ResultPredict.predict)
                      .joinedload(Predict.images),
                      joinedload(ResultPredict.user)
                  )
                  .filter(ResultPredict.user_id == user_id)
                  .order_by(ResultPredict.created_at.desc())
                  .all())

        formatted_results = []
        for result in results:
            predict_data = {
                'id': str(result.id),
                'status': result.status.value,
                'created_at': result.created_at.isoformat(),
                'predict': {
                    'id': str(result.predict.id),
                    'deskripsi': result.predict.deskripsi,
                    'images': [{
                        'id': str(image.id),
                        'name_image': image.name_image
                    } for image in result.predict.images]
                }
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
            ResultPredict.query
            .filter(ResultPredict.user_id == user_id)
            .order_by(ResultPredict.created_at.desc())
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

        result = (ResultPredict.query
                 .options(
                     joinedload(ResultPredict.predict)
                     .joinedload(Predict.images),
                     joinedload(ResultPredict.user)
                 )
                 .filter(
                     ResultPredict.user_id == user_id,
                     ResultPredict.id == predict_id
                 )
                .order_by(ResultPredict.created_at.desc())
                 .first())

        if not result:
            return jsonify({
                "error": True,
                "message": "Predict result not found.",
                "data": None
            }), 404

        detail_data = {
            'id': str(result.id),
            'status': result.status.value,
            'created_at': result.created_at.isoformat(),
            'updated_at': result.updated_at.isoformat(),
            'predict': {
                'id': str(result.predict.id),
                'deskripsi': result.predict.deskripsi,
                'created_at': result.predict.created_at.isoformat(),
                'images': [{
                    'id': str(image.id),
                    'name_image': image.name_image,
                    'created_at': image.created_at.isoformat()
                } for image in result.predict.images]
            },
            'user': {
                'name': result.user.name,
                'email': result.user.email,
                'address': result.user.address,
                'lang':result.user.lang,
                'lat':result.user.lat
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

        result = (ResultPredict.query
                 .options(
                     joinedload(ResultPredict.predict)
                     .joinedload(Predict.images),
                     joinedload(ResultPredict.user)
                 )
                 .filter(
                     ResultPredict.id == predict_id
                 )
                .order_by(ResultPredict.created_at.desc())
                .first())

        if not result:
            return jsonify({
                "error": True,
                "message": "Predict result not found.",
                "data": None
            }), 404

        detail_data = {
            'id': str(result.id),
            'status': result.status.value,
            'created_at': result.created_at.isoformat(),
            'updated_at': result.updated_at.isoformat(),
            'predict': {
                'id': str(result.predict.id),
                'deskripsi': result.predict.deskripsi,
                'created_at': result.predict.created_at.isoformat(),
                'images': [{
                    'id': str(image.id),
                    'name_image': image.name_image,
                    'created_at': image.created_at.isoformat()
                } for image in result.predict.images]
            },
            'user': {
                'name': result.user.name,
                'email': result.user.email,
                'address': result.user.address,
                'lang':result.user.lang,
                'lat':result.user.lat
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
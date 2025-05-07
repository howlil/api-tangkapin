# app/controllers/detection_controller

from app import db
from math import radians
from sqlalchemy import func
from app.models import User, CCTV, Predict, Images, StatusEnum, RoleEnum
from flask import request, jsonify
from sqlalchemy.orm import joinedload
from app.helpers.logger import setup_logger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import Float
from datetime import datetime
from app.utils.pusher_config import send_notification
from sqlalchemy import and_
from app.helpers.local_timezone import get_local_time

logger = setup_logger("detection")

local_time = get_local_time()

def update_status(predict_id, data):
    """
    Mengubah status laporan berdasarkan ID laporan.
    """
    try:
        new_status = data.get("status")

        # Validasi apakah status baru sesuai dengan enum StatusEnum
        if not new_status or new_status not in StatusEnum.__members__:
            return jsonify({"error": "Invalid status value"}), 400

        # Cari laporan berdasarkan ID
        laporan = Predict.query.filter_by(id=predict_id).first()

        if not laporan:
            return jsonify({"error": "Laporan not found"}), 404

        # Update status
        laporan.status = StatusEnum[new_status]
        db.session.commit()

        return jsonify({
            "message": "Status laporan berhasil diubah",
            "data": {
                "id": str(laporan.id),
                "status": laporan.status.value,
                "updated_at": laporan.updated_at
            }
        }), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify({"error": "Database error", "details": str(e)}), 500
    except Exception as e:
        return jsonify({"error": "An error occurred", "details": str(e)}), 500
    
    
def send_incident_notifications(owner, predict_id, nearby_police, images, address):
    """
    Fungsi untuk mengirim notifikasi ke owner dan police terdekat
    """
    try:
        logger.info("send notification owner")
        # Notifikasi ke owner
        owner_notification = {
            "type": "incident_detected",
            "report_id": str(predict_id),
            "message": f"Knife detected at your premises: {address}",
            "images": images[:1],  
            "timestamp": local_time
        }
        send_notification("owner", "incident_alert", owner_notification)

        # Notifikasi ke police terdekat
        logger.info("Sending notifications to police")
        for police in nearby_police:
            police_distance = getattr(police, 'distance', None)
            if police_distance is None:
                logger.error(f"Police object missing 'distance': {police}")
                continue

            police_notification = {
                "type": "incident_reported",
                "report_id": str(predict_id),
                "owner_name": getattr(owner, 'name', 'Unknown Owner'),
                "owner_address": address,
                "distance_km": round(police_distance, 2),  
                "images": images[:1],
                "timestamp": local_time
            }
            send_notification("police", "incident_alert", police_notification)

    except Exception as e:
        logger.error(f"Error sending notifications: {e}")
        

def get_owner_id_by_cctv_ip(cctv_ip):
    try:
        cctv = db.session.query(CCTV).options(joinedload(CCTV.user)).filter_by(cctv_ip=cctv_ip).first()
        if not cctv:
            return None
        return cctv.user_id
    except Exception as e:
        print(f"Error retrieving owner ID: {e}")
        return None
    
    
def create_report(owner_id, array_image, description):
    try:
        logger.info("Starting to create report...")

        if not owner_id or not array_image or not description:
            logger.error("Invalid input: Missing required fields.")
            return jsonify({"error": "Invalid input, all fields are required"}), 400

        # Cari user dengan role OWNER
        logger.info(f"Fetching owner with ID: {owner_id}")
        owner = db.session.query(User).filter(User.id == owner_id, User.role == RoleEnum.OWNER).first()
        if not owner or not owner.lat or not owner.lang:
            logger.error("Owner not found or coordinates missing.")
            return jsonify({"error": "Owner not found or invalid coordinates"}), 404

        # Ambil nilai koordinat OWNER
        owner_lat = float(owner.lat)
        owner_lang = float(owner.lang)
        logger.info(f"Owner coordinates: lat={owner_lat}, lang={owner_lang}")

        # Cari POLICE dalam radius 20 km menggunakan SQLAlchemy func
        logger.info("Finding nearby police within 20km radius...")
        nearby_police = db.session.query(
            User.id,
            User.name,
            (6371 * func.acos(
                func.cos(func.radians(owner_lat)) * func.cos(func.radians(User.lat.cast(Float))) *
                func.cos(func.radians(User.lang.cast(Float)) - func.radians(owner_lang)) +
                func.sin(func.radians(owner_lat)) * func.sin(func.radians(User.lat.cast(Float)))
            )).label("distance")
        ).filter(
            User.role == RoleEnum.POLICE,
            User.lat.isnot(None),
            User.lang.isnot(None),
            (6371 * func.acos(
                func.cos(func.radians(owner_lat)) * func.cos(func.radians(User.lat.cast(Float))) *
                func.cos(func.radians(User.lang.cast(Float)) - func.radians(owner_lang)) +
                func.sin(func.radians(owner_lat)) * func.sin(func.radians(User.lat.cast(Float)))
            )) <= 20
        ).all()

        if not nearby_police:
            logger.warning("No police found within 20km radius.")
            return jsonify({"error": "No police found within 20km radius"}), 404

        # Buat laporan Predict dengan status PENDING
        logger.info("Creating predict entry...")
        predict = Predict(
            user_id=owner.id,
            deskripsi=f"Telah terjadi perampokan di {owner.address} dari korban {owner.name}",
            status=StatusEnum.PENDING
        )
        db.session.add(predict)
        db.session.commit()
        logger.info(f"Predict entry created with ID: {predict.id}")

        # Simpan array image ke tabel Images
        logger.info("Saving images...")
        for image_name in array_image:
            image = Images(name_image=image_name, predict_id=predict.id)
            db.session.add(image)
        db.session.commit()
        logger.info("Images saved successfully.")

        # Laporan akhir
        logger.info("Building final report...")
        report = {
            "report_id": str(predict.id),
            "owner_id": str(owner.id),
            "address": str(owner.address),
            "description": description,
            "images": array_image,
            "created_at": local_time,
            "police_in_radius": [
                {"id": str(police.id), "name": police.name, "distance_km": round(police.distance, 2)}
                for police in nearby_police
            ]
        }
        
        logger.info("start send notification...")
        send_incident_notifications(
            owner=owner,
            predict_id=predict.id,
            nearby_police=nearby_police,
            images=array_image,
            address=owner.address
        )
   
        logger.info("Report created successfully.")
        return jsonify({"success": True, "report": report}), 201

    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        db.session.rollback()
        return jsonify({"error": "An unexpected error occurred"}), 500
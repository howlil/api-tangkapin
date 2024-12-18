from app import create_app, db
from app.models import User, RoleEnum, CCTV
from werkzeug.security import generate_password_hash
import uuid

def seed_users():
    with create_app().app_context():
        # Hash passwords
        owner_password = generate_password_hash("@Test123")
        police_password = generate_password_hash("@Test123")

        # Create Owner user
        owner = User(
            email="naufalse@gmail.com",
            name="Minimarket Naufal",
            password=owner_password,
            address="Jalan Dr.Moh. Hatta Simpang, Simp Jl. Pasia No.20, RT.01/RW.02, Kapala Koto, Kec. Pauh, Kota Padang, Sumatera Barat 25176",
            lang="-0.9261958",
            lat="100.43425",
            role=RoleEnum.OWNER,
            fcm_token="dummy_fcm_token_owner_12345",  # Tambahkan FCM token
            created_at=db.func.now(),
        )

        # Create Police user
        police = User(
            email="humas.polisi.pauah@gmail.com",
            name="Police Pauah",
            password=police_password,
            address="Jl. M. Hatta Pauh, Binuang Kp. Dalam, Kec. Pauh, Kota Padang, Sumatera Barat 25161",
            lang="-0.9299757",
            lat="100.4255762,20.24",
            role=RoleEnum.POLICE,
            fcm_token="dummy_fcm_token_police_67890",  # Tambahkan FCM token
            created_at=db.func.now(),
        )

        # Add to session
        db.session.add(owner)
        db.session.add(police)

        # Commit to database
        db.session.commit()

        print("Owner created:", owner.email)
        print("Police created:", police.email)


def seed_cctvs():
    with create_app().app_context():
        # Cari user "Naufal" berdasarkan email
        owner = User.query.filter_by(email="naufalse@gmail.com").first()

        if not owner:
            print("User with email 'naufalse@gmail.com' not found. Please seed users first.")
            return

        # Daftar CCTV yang akan ditambahkan
        cctvs_data = [
            {
                "cctv_ip": "https://192.168.1.7:8080",
                "nama_cctv": "CCTV Minimarket 1",
            },
            {
                "cctv_ip": "https://192.168.1.190:8080",
                "nama_cctv": "CCTV Minimarket 2",
            },
        ]

        # Tambahkan CCTV ke database
        for cctv in cctvs_data:
            new_cctv = CCTV(
                id=uuid.uuid4(),
                user_id=owner.id,  # Relasi ke user "Naufal"
                cctv_ip=cctv["cctv_ip"],
                nama_cctv=cctv["nama_cctv"],
                created_at=db.func.now(),
            )
            db.session.add(new_cctv)

        # Commit perubahan
        db.session.commit()

        print(f"CCTVs for user {owner.email} have been added successfully.")

if __name__ == "__main__":
    seed_users()
    seed_cctvs()

from . import db
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash
from enum import Enum  
import pytz
from sqlalchemy.types import TypeDecorator, DateTime



def jakarta_timezone():
    return pytz.timezone('Asia/Jakarta')

def get_jakarta_time():
    return datetime.now(jakarta_timezone())

class TimezoneAwareDateTime(TypeDecorator):
    impl = DateTime
    
    def process_bind_parameter(self, value, dialect):
        if value is not None and not value.tzinfo:
            return jakarta_timezone().localize(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and not value.tzinfo:
            return jakarta_timezone().localize(value)
        return value

class RoleEnum(Enum):
    OWNER = "OWNER"
    POLICE = "POLICE"

# Enum untuk Status
class StatusEnum(Enum):
    PENDING = "PENDING"
    DIPROSES = "DIPROSES"
    SELESAI = "SELESAI"

class User(db.Model):
    __tablename__ = "user"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String(100))
    password = db.Column(db.String(255), nullable=False)
    address = db.Column(db.String(255))
    lang = db.Column(db.String(50))
    lat = db.Column(db.String(50))
    fcm_token = db.Column(db.String, nullable=True) 
    role = db.Column(db.Enum(RoleEnum), nullable=False) 
    created_at = db.Column(TimezoneAwareDateTime, default=get_jakarta_time)
    updated_at = db.Column(TimezoneAwareDateTime, onupdate=get_jakarta_time, default=get_jakarta_time)


    # Relationships
    @staticmethod
    def hash_password(password):
        return generate_password_hash(password)

    tokens = db.relationship("Token", back_populates="user", cascade="all, delete-orphan")
    result_predicts = db.relationship("ResultPredict", back_populates="user", cascade="all, delete-orphan")
    cctvs = db.relationship("CCTV", back_populates="user", cascade="all, delete-orphan")


# Token Model
class Token(db.Model):
    __tablename__ = "tokens"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    token = db.Column(db.String(255), nullable=False)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(TimezoneAwareDateTime, default=get_jakarta_time)
    updated_at = db.Column(TimezoneAwareDateTime, onupdate=get_jakarta_time, default=get_jakarta_time)

    
    # Relationships
    user = db.relationship("User", back_populates="tokens")

# ResultPredict Model
class ResultPredict(db.Model):
    __tablename__ = "result_predicts"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.id"), nullable=False)
    predict_id = db.Column(UUID(as_uuid=True), db.ForeignKey("predicts.id"), unique=True, nullable=False)
    status = db.Column(db.Enum(StatusEnum), nullable=False)
    created_at = db.Column(TimezoneAwareDateTime, default=get_jakarta_time)
    updated_at = db.Column(TimezoneAwareDateTime, onupdate=get_jakarta_time, default=get_jakarta_time)

    
    # Relationships
    user = db.relationship("User", back_populates="result_predicts")
    predict = db.relationship("Predict", back_populates="result")

# Predict Model
class Predict(db.Model):
    __tablename__ = "predicts"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deskripsi = db.Column(db.Text, nullable=False)
    created_at = db.Column(TimezoneAwareDateTime, default=get_jakarta_time)
    updated_at = db.Column(TimezoneAwareDateTime, onupdate=get_jakarta_time, default=get_jakarta_time)

    
    # Relationships
    images = db.relationship("Images", back_populates="predict", cascade="all, delete-orphan")
    result = db.relationship("ResultPredict", back_populates="predict", uselist=False)

# CCTV Model
class CCTV(db.Model):
    __tablename__ = "cctvs"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey("user.id"), nullable=False)
    cctv_ip = db.Column(db.String, unique=True, nullable=False, index=True)  # Tambahkan indeks
    nama_cctv = db.Column(db.String, unique=True, nullable=False)
    created_at = db.Column(TimezoneAwareDateTime, default=get_jakarta_time)
    updated_at = db.Column(TimezoneAwareDateTime, onupdate=get_jakarta_time, default=get_jakarta_time)

    
    # Relationships
    user = db.relationship("User", back_populates="cctvs")


# Images Model
class Images(db.Model):
    __tablename__ = "images"
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name_image = db.Column(db.String, nullable=False, index=True) 
    predict_id = db.Column(UUID(as_uuid=True), db.ForeignKey("predicts.id"), nullable=False)
    created_at = db.Column(TimezoneAwareDateTime, default=get_jakarta_time)
    updated_at = db.Column(TimezoneAwareDateTime, onupdate=get_jakarta_time, default=get_jakarta_time)

    # Relationships
    predict = db.relationship("Predict", back_populates="images")

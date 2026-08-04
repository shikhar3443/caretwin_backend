import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Enum, Text, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class MetricType(str, enum.Enum):
    BP_SYS = "BP_SYS"
    BP_DIA = "BP_DIA"
    FASTING_GLUCOSE = "FASTING_GLUCOSE"
    RANDOM_GLUCOSE = "RANDOM_GLUCOSE"
    HBA1C = "HBA1C"
    HEMOGLOBIN = "HEMOGLOBIN"
    CHOLESTEROL = "CHOLESTEROL"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    family_members = relationship("FamilyMember", back_populates="user", cascade="all, delete-orphan")

class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    relationship = Column(String(50), nullable=False) # e.g. Self, Father, Mother, Child
    gender = Column(String(20), nullable=True)
    dob = Column(String(20), nullable=True)
    blood_group = Column(String(10), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="family_members")
    medical_records = relationship("MedicalRecord", back_populates="family_member", cascade="all, delete-orphan")
    measurements = relationship("Measurement", back_populates="family_member", cascade="all, delete-orphan")
    trend_alerts = relationship("TrendAlert", back_populates="family_member", cascade="all, delete-orphan")

class MedicalRecord(Base):
    __tablename__ = "medical_records"

    id = Column(Integer, primary_key=True, index=True)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)
    title = Column(String(200), nullable=False)
    document_type = Column(String(50), default="Prescription") # Prescription, Lab Report, Discharge Summary
    file_path = Column(String(500), nullable=False)
    upload_date = Column(DateTime, default=datetime.utcnow)
    ocr_status = Column(String(50), default="COMPLETED") # PENDING, PROCESSING, COMPLETED, FAILED

    family_member = relationship("FamilyMember", back_populates="medical_records")
    measurements = relationship("Measurement", back_populates="record", cascade="all, delete-orphan")

class Measurement(Base):
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)
    record_id = Column(Integer, ForeignKey("medical_records.id"), nullable=True)
    metric_type = Column(String(50), nullable=False) # MetricType string
    value_numeric = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False) # mmHg, mg/dL, g/dL, %
    recorded_date = Column(DateTime, default=datetime.utcnow)

    family_member = relationship("FamilyMember", back_populates="measurements")
    record = relationship("MedicalRecord", back_populates="measurements")

class TrendAlert(Base):
    __tablename__ = "trend_alerts"

    id = Column(Integer, primary_key=True, index=True)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)
    metric_type = Column(String(50), nullable=False)
    risk_level = Column(String(20), default="MEDIUM")
    message = Column(Text, nullable=False)
    flagged_date = Column(DateTime, default=datetime.utcnow)
    is_acknowledged = Column(Boolean, default=False)

    family_member = relationship("FamilyMember", back_populates="trend_alerts")

class DoctorShare(Base):
    __tablename__ = "doctor_shares"

    id = Column(Integer, primary_key=True, index=True)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False)
    access_code = Column(String(50), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

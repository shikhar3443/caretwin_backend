"""Emergency QR models. Import this module wherever Base.metadata.create_all runs
(e.g. app/main.py) so the tables get created."""
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text

from app.core.database import Base  # adjust if your Base lives elsewhere


def _now():
    return datetime.now(timezone.utc)


class EmergencyProfile(Base):
    """Minimum medical data needed for immediate treatment (one per family member)."""
    __tablename__ = "emergency_profiles"

    id = Column(Integer, primary_key=True, index=True)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), unique=True, nullable=False)

    blood_group = Column(String(5))                 # e.g. "O+"
    allergies = Column(Text, default="")            # comma-separated, drug allergies first
    chronic_conditions = Column(Text, default="")   # diabetes, epilepsy, heart disease...
    current_medications = Column(Text, default="")  # critical ones: insulin, blood thinners...
    implants_devices = Column(Text, default="")     # pacemaker, stents...
    is_pregnant = Column(Boolean, default=False)
    organ_donor = Column(Boolean, default=False)
    emergency_contact_name = Column(String(100))
    emergency_contact_phone = Column(String(30))
    notes = Column(Text, default="")                # short, e.g. "No blood transfusion"
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now)


class EmergencyQRToken(Base):
    """Only the SHA-256 hash of the token is stored; the raw token lives only in the QR."""
    __tablename__ = "emergency_qr_tokens"

    id = Column(Integer, primary_key=True)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False, index=True)
    token_hash = Column(String(64), unique=True, index=True, nullable=False)
    revoked = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)


class EmergencyAccessLog(Base):
    __tablename__ = "emergency_access_logs"

    id = Column(Integer, primary_key=True)
    family_member_id = Column(Integer, ForeignKey("family_members.id"), nullable=False, index=True)
    accessed_at = Column(DateTime(timezone=True), default=_now)
    ip_address = Column(String(64))
    user_agent = Column(String(255))

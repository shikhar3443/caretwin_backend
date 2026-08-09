from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

# Auth Schemas
class UserRegister(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Family Member Schemas
class FamilyMemberCreate(BaseModel):
    name: str
    relationship: str
    gender: Optional[str] = None
    dob: Optional[str] = None
    blood_group: Optional[str] = None

class FamilyMemberOut(BaseModel):
    id: int
    user_id: int
    name: str
    relationship: str
    gender: Optional[str] = None
    dob: Optional[str] = None
    blood_group: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Medical Record Schemas
class MedicalRecordOut(BaseModel):
    id: int
    family_member_id: int
    title: str
    document_type: str
    file_path: str
    upload_date: datetime
    ocr_status: str

    model_config = ConfigDict(from_attributes=True)

# Measurement Schemas
class MeasurementCreate(BaseModel):
    family_member_id: int
    record_id: Optional[int] = None
    metric_type: str
    value_numeric: float
    unit: str
    recorded_date: Optional[datetime] = None

class MeasurementOut(BaseModel):
    id: int
    family_member_id: int
    record_id: Optional[int] = None
    metric_type: str
    value_numeric: float
    unit: str
    recorded_date: datetime

    model_config = ConfigDict(from_attributes=True)

# Trend Alert Schemas
class TrendAlertOut(BaseModel):
    id: int
    family_member_id: int
    metric_type: str
    risk_level: str
    message: str
    flagged_date: datetime
    is_acknowledged: bool

    model_config = ConfigDict(from_attributes=True)

# OCR Processing Payload Schema (For Teammate Integration)
class ExtractedField(BaseModel):
    metric_type: str
    value_numeric: float
    unit: str
    recorded_date: Optional[datetime] = None

class OCRProcessResponse(BaseModel):
    record_id: int
    extracted_fields: List[ExtractedField]
    raw_text: Optional[str] = None

# Doctor Share Schema
class DoctorShareCreate(BaseModel):
    family_member_id: int
    duration_hours: int = 24

class DoctorShareOut(BaseModel):
    access_code: str
    expires_at: datetime
    share_url: str

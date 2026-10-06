from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class EmergencyProfileIn(BaseModel):
    blood_group: Optional[str] = None
    allergies: str = ""
    chronic_conditions: str = ""
    current_medications: str = ""
    implants_devices: str = ""
    is_pregnant: bool = False
    organ_donor: bool = False
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: str = ""


class EmergencyProfileOut(EmergencyProfileIn):
    model_config = ConfigDict(from_attributes=True)
    updated_at: Optional[datetime] = None


class EmergencyPublicView(BaseModel):
    """What a scanner sees. Deliberately excludes address, ID numbers, insurance, full history."""
    name: str
    age: Optional[int] = None
    sex: Optional[str] = None
    blood_group: Optional[str] = None
    allergies: List[str] = []
    chronic_conditions: List[str] = []
    current_medications: List[str] = []
    implants_devices: List[str] = []
    is_pregnant: bool = False
    organ_donor: bool = False
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    notes: str = ""


class QRIssueOut(BaseModel):
    emergency_url: str
    qr_png_base64: str
    note: str = "Shown once. Regenerating invalidates all older QR codes for this member."


class AccessLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    accessed_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

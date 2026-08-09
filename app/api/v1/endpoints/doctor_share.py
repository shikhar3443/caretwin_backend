import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.models import User, FamilyMember, DoctorShare, Measurement, MedicalRecord
from app.schemas.schemas import DoctorShareCreate, DoctorShareOut

router = APIRouter(prefix="/share", tags=["Doctor Decision Support"])

@router.post("/generate", response_model=DoctorShareOut)
def generate_doctor_share_link(
    share_in: DoctorShareCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(FamilyMember).filter(
        FamilyMember.id == share_in.family_member_id,
        FamilyMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member profile not found")

    code = uuid.uuid4().hex[:8].upper()
    expiry = datetime.utcnow() + timedelta(hours=share_in.duration_hours)

    share = DoctorShare(
        family_member_id=share_in.family_member_id,
        access_code=code,
        expires_at=expiry
    )
    db.add(share)
    db.commit()

    return DoctorShareOut(
        access_code=code,
        expires_at=expiry,
        share_url=f"/api/v1/share/view/{code}"
    )

@router.get("/view/{access_code}")
def doctor_view_timeline(access_code: str, db: Session = Depends(get_db)):
    share = db.query(DoctorShare).filter(DoctorShare.access_code == access_code).first()
    if not share or share.expires_at < datetime.utcnow():
        raise HTTPException(status_code=403, detail="Invalid or expired doctor access code")

    member = db.query(FamilyMember).filter(FamilyMember.id == share.family_member_id).first()
    measurements = db.query(Measurement).filter(
        Measurement.family_member_id == share.family_member_id
    ).order_by(Measurement.recorded_date.asc()).all()

    records = db.query(MedicalRecord).filter(
        MedicalRecord.family_member_id == share.family_member_id
    ).all()

    return {
        "patient": {
            "name": member.name,
            "gender": member.gender,
            "dob": member.dob,
            "blood_group": member.blood_group
        },
        "timeline_measurements": measurements,
        "records_count": len(records),
        "access_expires_at": share.expires_at
    }

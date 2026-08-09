import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.api.v1.endpoints.auth import get_current_user
from app.models.models import User, FamilyMember, MedicalRecord
from app.schemas.schemas import MedicalRecordOut

router = APIRouter(prefix="/records", tags=["Smart Record Locker"])

@router.post("/upload", response_model=MedicalRecordOut, status_code=status.HTTP_201_CREATED)
async def upload_medical_record(
    family_member_id: int = Form(...),
    title: str = Form(...),
    document_type: str = Form("Prescription"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Verify ownership of family member profile
    member = db.query(FamilyMember).filter(
        FamilyMember.id == family_member_id,
        FamilyMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member profile not found")

    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)

    record = MedicalRecord(
        family_member_id=family_member_id,
        title=title,
        document_type=document_type,
        file_path=file_path,
        ocr_status="PENDING"
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return record

@router.get("", response_model=List[MedicalRecordOut])
def list_medical_records(
    family_member_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(MedicalRecord).join(FamilyMember).filter(FamilyMember.user_id == current_user.id)
    if family_member_id:
        query = query.filter(MedicalRecord.family_member_id == family_member_id)
    return query.order_by(MedicalRecord.upload_date.desc()).all()

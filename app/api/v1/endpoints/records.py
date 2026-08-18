import os
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
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
    document_type: str = Form("Prescription"), # Prescription, Lab Report, Discharge Summary, Radiology
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

    # Allowed extensions check
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{ext}'. Allowed formats: PDF, PNG, JPG, JPEG"
        )

    # Generate unique filename to prevent collisions
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_filename)

    # Save file contents
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
    document_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(MedicalRecord).join(FamilyMember).filter(FamilyMember.user_id == current_user.id)
    
    if family_member_id:
        query = query.filter(MedicalRecord.family_member_id == family_member_id)
    if document_type:
        query = query.filter(MedicalRecord.document_type == document_type)

    return query.order_by(MedicalRecord.upload_date.desc()).all()

@router.get("/{record_id}", response_model=MedicalRecordOut)
def get_medical_record_detail(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(MedicalRecord).join(FamilyMember).filter(
        MedicalRecord.id == record_id,
        FamilyMember.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")

    return record

@router.get("/{record_id}/download")
def download_medical_record_file(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(MedicalRecord).join(FamilyMember).filter(
        MedicalRecord.id == record_id,
        FamilyMember.user_id == current_user.id
    ).first()

    if not record or not os.path.exists(record.file_path):
        raise HTTPException(status_code=404, detail="Medical record file not found")

    return FileResponse(path=record.file_path, filename=os.path.basename(record.file_path))

@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medical_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(MedicalRecord).join(FamilyMember).filter(
        MedicalRecord.id == record_id,
        FamilyMember.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")

    # Clean up file on disk if exists
    if os.path.exists(record.file_path):
        os.remove(record.file_path)

    db.delete(record)
    db.commit()
    return None

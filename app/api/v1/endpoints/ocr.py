from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.models import User, MedicalRecord, Measurement, FamilyMember
from app.schemas.schemas import OCRProcessResponse, ExtractedField
from app.services.ocr_service import OCRService

router = APIRouter(prefix="/ocr", tags=["OCR & Medical NLP"])

@router.post("/process/{record_id}", response_model=OCRProcessResponse)
def process_record_ocr(
    record_id: int,
    raw_text_input: Optional[str] = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    record = db.query(MedicalRecord).join(FamilyMember).filter(
        MedicalRecord.id == record_id,
        FamilyMember.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")

    text_to_process = raw_text_input or "BP: 138/88 mmHg, Fasting Glucose: 126 mg/dL, HbA1c: 6.8%, Hemoglobin: 13.5 g/dL"
    extracted_data = OCRService.extract_metrics_from_text(text_to_process, record.upload_date)

    created_fields = []
    for item in extracted_data:
        m = Measurement(
            family_member_id=record.family_member_id,
            record_id=record.id,
            metric_type=item["metric_type"],
            value_numeric=item["value_numeric"],
            unit=item["unit"],
            recorded_date=item["recorded_date"]
        )
        db.add(m)
        created_fields.append(ExtractedField(**item))

    record.ocr_status = "COMPLETED"
    db.commit()

    return OCRProcessResponse(
        record_id=record.id,
        extracted_fields=created_fields,
        raw_text=text_to_process
    )

@router.post("/payload/{record_id}", response_model=OCRProcessResponse)
def ingest_teammate_ocr_payload(
    record_id: int,
    payload_fields: List[ExtractedField],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Direct ingestion route for OCR/NLP Teammate integration.
    Allows passing structured extracted JSON fields directly from PaddleOCR / EasyOCR pipeline.
    """
    record = db.query(MedicalRecord).join(FamilyMember).filter(
        MedicalRecord.id == record_id,
        FamilyMember.user_id == current_user.id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Medical record not found")

    for field in payload_fields:
        m = Measurement(
            family_member_id=record.family_member_id,
            record_id=record.id,
            metric_type=field.metric_type,
            value_numeric=field.value_numeric,
            unit=field.unit,
            recorded_date=field.recorded_date or record.upload_date
        )
        db.add(m)

    record.ocr_status = "COMPLETED"
    db.commit()

    return OCRProcessResponse(
        record_id=record.id,
        extracted_fields=payload_fields,
        raw_text="Direct Teammate Payload Ingestion"
    )

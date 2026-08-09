from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
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

    text_to_process = raw_text_input or "BP: 142/92 mmHg, Fasting Glucose: 132 mg/dL, HbA1c: 6.9%"
    extracted_data = OCRService.extract_metrics_from_text(text_to_process)

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

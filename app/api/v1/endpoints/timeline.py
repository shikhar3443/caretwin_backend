from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.models import User, FamilyMember, Measurement
from app.schemas.schemas import MeasurementOut, MeasurementCreate

router = APIRouter(prefix="/timeline", tags=["Health Timeline"])

@router.get("/{family_member_id}", response_model=List[MeasurementOut])
def get_health_timeline(
    family_member_id: int,
    metric_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(FamilyMember).filter(
        FamilyMember.id == family_member_id,
        FamilyMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member profile not found")

    query = db.query(Measurement).filter(Measurement.family_member_id == family_member_id)
    if metric_type:
        query = query.filter(Measurement.metric_type == metric_type)

    return query.order_by(Measurement.recorded_date.asc()).all()

@router.post("/measurement", response_model=MeasurementOut)
def add_manual_measurement(
    measurement_in: MeasurementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(FamilyMember).filter(
        FamilyMember.id == measurement_in.family_member_id,
        FamilyMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member profile not found")

    m = Measurement(
        family_member_id=measurement_in.family_member_id,
        record_id=measurement_in.record_id,
        metric_type=measurement_in.metric_type,
        value_numeric=measurement_in.value_numeric,
        unit=measurement_in.unit,
        recorded_date=measurement_in.recorded_date
    )
    db.add(m)
    db.commit()
    db.refresh(m)
    return m

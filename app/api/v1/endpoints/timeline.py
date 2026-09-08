from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
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

@router.get("/{family_member_id}/summary")
def get_timeline_summary_metrics(
    family_member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Summary analytics endpoint for Frontend dashboard cards.
    Returns latest value, min, max, average, and reading count per metric type.
    """
    member = db.query(FamilyMember).filter(
        FamilyMember.id == family_member_id,
        FamilyMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member profile not found")

    measurements = db.query(Measurement).filter(
        Measurement.family_member_id == family_member_id
    ).all()

    summary_by_metric: Dict[str, Any] = {}

    for m in measurements:
        m_type = m.metric_type
        if m_type not in summary_by_metric:
            summary_by_metric[m_type] = {
                "metric_type": m_type,
                "unit": m.unit,
                "values": [],
                "latest_value": m.value_numeric,
                "latest_date": m.recorded_date
            }
        summary_by_metric[m_type]["values"].append(m.value_numeric)
        if m.recorded_date > summary_by_metric[m_type]["latest_date"]:
            summary_by_metric[m_type]["latest_value"] = m.value_numeric
            summary_by_metric[m_type]["latest_date"] = m.recorded_date

    result = []
    for m_type, data in summary_by_metric.items():
        vals = data["values"]
        result.append({
            "metric_type": m_type,
            "unit": data["unit"],
            "latest": data["latest_value"],
            "latest_date": data["latest_date"],
            "min": min(vals),
            "max": max(vals),
            "avg": round(sum(vals) / len(vals), 2),
            "count": len(vals)
        })

    return {
        "family_member_id": family_member_id,
        "patient_name": member.name,
        "metrics_summary": result
    }

@router.post("/measurement", response_model=MeasurementOut, status_code=status.HTTP_201_CREATED)
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

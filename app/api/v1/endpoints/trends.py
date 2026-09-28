from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.models import User, FamilyMember, TrendAlert
from app.services.trend_engine import TrendDetectionEngine

router = APIRouter(prefix="/trends", tags=["Trend Detection & Risk Flags"])


# ---------------------------------------------------------------------------
# Response schemas (inline — no need to pollute global schemas.py)
# ---------------------------------------------------------------------------
class TrendAlertOut(BaseModel):
    id: int
    metric_type: str
    risk_level: str
    message: str
    flagged_date: datetime
    is_acknowledged: bool

    class Config:
        from_attributes = True


class TrendEvaluateResponse(BaseModel):
    family_member_id: int
    new_alerts: int
    alerts: List[TrendAlertOut]


class AcknowledgeResponse(BaseModel):
    alert_id: int
    acknowledged: bool


# ---------------------------------------------------------------------------
# POST /trends/evaluate/{family_member_id}
# Runs the trend engine and persists new alerts to DB.
# ---------------------------------------------------------------------------
@router.post("/evaluate/{family_member_id}", response_model=TrendEvaluateResponse)
def evaluate_trends(
    family_member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Analyse all measurements for a family member and generate risk alerts
    if 3+ consecutive rising/falling readings are detected.
    """
    # Ownership check
    member = db.query(FamilyMember).filter(
        FamilyMember.id == family_member_id,
        FamilyMember.user_id == current_user.id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    new_alerts = TrendDetectionEngine.evaluate_family_member_trends(db, family_member_id)

    return TrendEvaluateResponse(
        family_member_id=family_member_id,
        new_alerts=len(new_alerts),
        alerts=[TrendAlertOut.model_validate(a) for a in new_alerts],
    )


# ---------------------------------------------------------------------------
# GET /trends/{family_member_id}
# Fetch all active (unacknowledged) alerts for the notification bell.
# ---------------------------------------------------------------------------
@router.get("/{family_member_id}", response_model=List[TrendAlertOut])
def get_active_alerts(
    family_member_id: int,
    include_acknowledged: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns trend alerts for a family member.
    Default: only unacknowledged (for notification bell).
    Pass ?include_acknowledged=true for full history.
    """
    member = db.query(FamilyMember).filter(
        FamilyMember.id == family_member_id,
        FamilyMember.user_id == current_user.id,
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member not found")

    query = db.query(TrendAlert).filter(TrendAlert.family_member_id == family_member_id)
    if not include_acknowledged:
        query = query.filter(TrendAlert.is_acknowledged == False)  # noqa: E712
    alerts = query.order_by(TrendAlert.flagged_date.desc()).all()
    return [TrendAlertOut.model_validate(a) for a in alerts]


# ---------------------------------------------------------------------------
# PATCH /trends/acknowledge/{alert_id}
# Mark an alert as read (notification bell dismiss).
# ---------------------------------------------------------------------------
@router.patch("/acknowledge/{alert_id}", response_model=AcknowledgeResponse)
def acknowledge_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Dismiss a trend alert from the notification bell."""
    alert = (
        db.query(TrendAlert)
        .join(FamilyMember)
        .filter(TrendAlert.id == alert_id, FamilyMember.user_id == current_user.id)
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_acknowledged = True
    db.commit()
    return AcknowledgeResponse(alert_id=alert_id, acknowledged=True)

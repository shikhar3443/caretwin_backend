from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.models import User, FamilyMember, TrendAlert
from app.schemas.schemas import TrendAlertOut
from app.services.trend_engine import TrendDetectionEngine

router = APIRouter(prefix="/trends", tags=["AI Trend Detection"])

@router.post("/evaluate/{family_member_id}", response_model=List[TrendAlertOut])
def evaluate_trends(
    family_member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(FamilyMember).filter(
        FamilyMember.id == family_member_id,
        FamilyMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member profile not found")

    TrendDetectionEngine.evaluate_family_member_trends(db, family_member_id)
    return db.query(TrendAlert).filter(TrendAlert.family_member_id == family_member_id).all()

@router.get("/alerts/{family_member_id}", response_model=List[TrendAlertOut])
def get_alerts(
    family_member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(FamilyMember).filter(
        FamilyMember.id == family_member_id,
        FamilyMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member profile not found")

    return db.query(TrendAlert).filter(
        TrendAlert.family_member_id == family_member_id
    ).order_by(TrendAlert.flagged_date.desc()).all()

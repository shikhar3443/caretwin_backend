from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.models import User, FamilyMember
from app.schemas.schemas import FamilyMemberCreate, FamilyMemberOut

router = APIRouter(prefix="/family", tags=["Family Profiles"])

@router.get("", response_model=List[FamilyMemberOut])
def get_family_members(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(FamilyMember).filter(FamilyMember.user_id == current_user.id).all()

@router.post("", response_model=FamilyMemberOut, status_code=status.HTTP_201_CREATED)
def create_family_member(
    member_in: FamilyMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = FamilyMember(
        user_id=current_user.id,
        name=member_in.name,
        relationship=member_in.relationship,
        gender=member_in.gender,
        dob=member_in.dob,
        blood_group=member_in.blood_group
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

@router.get("/{member_id}", response_model=FamilyMemberOut)
def get_family_member_detail(
    member_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    member = db.query(FamilyMember).filter(
        FamilyMember.id == member_id,
        FamilyMember.user_id == current_user.id
    ).first()
    if not member:
        raise HTTPException(status_code=404, detail="Family member profile not found")
    return member

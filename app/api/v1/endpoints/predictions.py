from typing import Dict, List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from app.api.v1.endpoints.auth import get_current_user
from app.models.models import User
from app.services.prediction_service import get_prediction_schema, predict_mortality

router = APIRouter(prefix="/predictions", tags=["ML Mortality & Risk Predictions"])


class MortalityPredictRequest(BaseModel):
    age: float = Field(ge=0, le=120)
    gender: Optional[str] = None
    admissionType: Optional[str] = None
    admission_type: Optional[str] = None
    admissionLocation: Optional[str] = None
    admission_location: Optional[str] = None
    insurance: Optional[str] = None
    language: Optional[str] = None
    maritalStatus: Optional[str] = None
    marital_status: Optional[str] = None
    race: Optional[str] = None
    admissionDate: Optional[str] = None
    admission_date: Optional[str] = None
    admissionTime: Optional[str] = None
    admission_time: Optional[str] = None
    labs: Dict[str, List[float]] = Field(default_factory=dict)


@router.get("/schema")
def get_schema(current_user: User = Depends(get_current_user)):
    """Returns the ML model prediction window, supported labs, and allowed categorical fields."""
    return get_prediction_schema()


@router.post("/mortality")
def predict_mortality_endpoint(
    req: MortalityPredictRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Computes mortality risk probability using trained XGBoost model.
    Matches the schema expected by CareTwin frontend.
    """
    try:
        result = predict_mortality(req.model_dump())
        return {"result": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )

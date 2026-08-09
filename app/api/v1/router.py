from fastapi import APIRouter
from app.api.v1.endpoints import auth, family, records, ocr, timeline, trends, doctor_share

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(family.router)
api_router.include_router(records.router)
api_router.include_router(ocr.router)
api_router.include_router(timeline.router)
api_router.include_router(trends.router)
api_router.include_router(doctor_share.router)

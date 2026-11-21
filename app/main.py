from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router
from app.api.v1.endpoints.emergency import public_page_router
import app.models.emergency  # registers emergency_profiles, emergency_qr_tokens, emergency_access_logs

# Automatically initialize database tables on startup
Base.metadata.create_all(bind=engine)

def _migrate_db_columns():
    """Ensure any newly added columns exist in existing SQLite/Postgres tables."""
    with engine.connect() as conn:
        try:
            for col, col_type in [
                ("quality_status", "VARCHAR(50)"),
                ("ocr_confidence", "FLOAT"),
                ("diagnosis", "TEXT"),
                ("medications", "TEXT")
            ]:
                try:
                    conn.execute(f"ALTER TABLE medical_records ADD COLUMN {col} {col_type}")
                    conn.commit()
                except Exception:
                    pass  # column already exists
        except Exception:
            pass

_migrate_db_columns()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    description="CareTwin Backend REST APIs - AI-Powered Personal Healthcare Record Management System"
)

# Enable CORS for Frontend integration with regex origin matching for localhost & 127.0.0.1
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:[0-9]+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(public_page_router)

@app.get("/", tags=["Health Check"])
def root():
    return {
        "status": "online",
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs"
    }

# CareTwin Backend - Personal Healthcare Record Management System

CareTwin is an AI-powered Personal Healthcare Record (PHR) Management System designed to consolidate fragmented medical records into a unified, longitudinal health story.

---

## 🎯 Week 3 Focus & Deliverables: Smart Record Locker API

In Week 3, we built the **Smart Record Locker** (Slide 5: Feature 01), allowing users to upload and manage medical documents safely:

### 📁 1. Record Upload & Management (`/api/v1/records`)
- **`POST /api/v1/records/upload`**: Accepts `multipart/form-data` uploads (PDF, PNG, JPG). Validates document extension, generates UUID filenames to avoid naming collisions, and registers record metadata with `ocr_status = "PENDING"`.
- **`GET /api/v1/records`**: Lists medical records for the logged-in user, with optional filters by `family_member_id` and `document_type` (Prescription, Lab Report, Discharge Summary, Radiology).
- **`GET /api/v1/records/{record_id}`**: Retrieves metadata for a specific record.
- **`GET /api/v1/records/{record_id}/download`**: Securely streams the actual document file for viewing/downloading.
- **`DELETE /api/v1/records/{record_id}`**: Deletes the record metadata from DB and cleans up the associated file on disk.

---

## 🧪 Testing Week 3 APIs
Run automated Pytest suite for Smart Record Locker:
```bash
python -m pytest tests/test_records.py -v
```

---

## 📁 Repository Structure (Week 3)
```
caretwin-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py         # Registration, Login, JWT auth
│   │       │   ├── family.py       # Family member profiles CRUD
│   │       │   └── records.py      # Smart Record Locker APIs
│   │       └── router.py           # V1 API router
│   ├── core/
│   │   ├── config.py               # Pydantic Settings
│   │   ├── database.py             # SQLAlchemy Engine & Session
│   │   └── security.py             # Bcrypt hashing & JWT functions
│   ├── models/
│   │   └── models.py               # Database schemas
│   ├── schemas/
│   │   └── schemas.py              # Pydantic validation schemas
│   └── main.py                     # FastAPI app entrypoint
├── tests/
│   ├── test_auth_family.py         # Week 2 unit tests
│   └── test_records.py             # Week 3 Record Locker unit tests
├── uploads/                        # Document upload directory
├── .gitignore
├── requirements.txt
└── README.md
```

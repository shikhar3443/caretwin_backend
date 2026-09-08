# CareTwin Backend - Personal Healthcare Record Management System

CareTwin is an AI-powered Personal Healthcare Record (PHR) Management System designed to consolidate fragmented medical records into a unified, longitudinal health story.

---

## 🎯 Week 4 Focus & Deliverables: OCR & Medical NLP Pipeline

In Week 4, we implemented the automated document extraction pipeline (Slide 11):

### 🔬 1. Medical NLP & Parsing Service (`app/services/ocr_service.py`)
- Regex and clinical pattern matching to extract Systolic BP, Diastolic BP, Fasting Blood Glucose, HbA1c, Hemoglobin, and Total Cholesterol.
- Standardizes metrics into numerical values and medical units (`mmHg`, `mg/dL`, `%`, `g/dL`).

### 🤖 2. OCR API Integration (`/api/v1/ocr`)
- **`POST /api/v1/ocr/process/{record_id}`**: Triggers parsing on uploaded document text, updates `ocr_status = "COMPLETED"`, and inserts structured metrics into the DB.
- **`POST /api/v1/ocr/payload/{record_id}`**: Direct integration webhook for PaddleOCR / EasyOCR teammate to ingest pre-parsed JSON.

---

## 🎯 Week 5 Focus & Deliverables: Health Timeline Engine

In Week 5, we built the longitudinal time-series health timeline (Slide 6: Feature 02):

### 📈 1. Timeline & Analytics APIs (`/api/v1/timeline`)
- **`GET /api/v1/timeline/{family_member_id}`**: Returns chronological readings sorted by recorded date for visualization on React charts. Supports `metric_type` filter.
- **`GET /api/v1/timeline/{family_member_id}/summary`**: Returns min, max, average, latest value, and reading count per metric type for dashboard summary cards.
- **`POST /api/v1/timeline/measurement`**: Allows patients to manually log a blood pressure or glucose reading.

---

## 🧪 Testing Weeks 4 & 5 APIs
Run automated Pytest suite for OCR and Timeline pipelines:
```bash
python -m pytest tests/test_ocr_timeline.py -v
```

---

## 📁 Repository Structure (Weeks 4 & 5)
```
caretwin-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py         # Registration, Login, JWT auth
│   │       │   ├── family.py       # Family member profiles CRUD
│   │       │   ├── records.py      # Smart Record Locker APIs
│   │       │   ├── ocr.py          # OCR & Medical NLP APIs
│   │       │   └── timeline.py     # Health Timeline APIs
│   │       └── router.py           # V1 API router
│   ├── core/
│   ├── models/
│   ├── schemas/
│   └── services/
│       └── ocr_service.py          # Medical NLP Regex & Parsing rules
├── tests/
│   ├── test_auth_family.py         # Week 2 unit tests
│   ├── test_records.py             # Week 3 unit tests
│   └── test_ocr_timeline.py        # Weeks 4 & 5 unit tests
├── uploads/
├── .gitignore
├── requirements.txt
└── README.md
```

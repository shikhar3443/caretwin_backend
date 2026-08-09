# CareTwin Backend - Personal Healthcare Record Management System

CareTwin is an AI-powered Personal Healthcare Record (PHR) Management System designed to consolidate fragmented medical records into a unified, longitudinal health story.

---

## 🎯 Week 2 Focus & Deliverables: Auth & Family Profiles API

In Week 2, we implemented complete Authentication and multi-profile Family Management:

### 🔑 1. Authentication Engine (`/api/v1/auth`)
- **`POST /api/v1/auth/register`**: Secure user registration. Hashes passwords using **Bcrypt** (`passlib`) and automatically generates a default `'Self'` family profile.
- **`POST /api/v1/auth/login`**: Authenticates user credentials and issues a signed **JWT Access Token** (`python-jose`).
- **`GET /api/v1/auth/me`**: Protected route returning current logged-in user details.

### 👨‍👩‍👧‍👦 2. Family Profiles Engine (`/api/v1/family`)
- **`POST /api/v1/family`**: Adds independent family member profiles (Father, Mother, Child, Spouse) under a single primary account.
- **`GET /api/v1/family`**: Retrieves all family profiles linked to the current user.
- **`GET /api/v1/family/{member_id}`**: Fetches details for a specific family profile with strict user-level data isolation (zero data mixing).

---

## 🧪 Testing Week 2 APIs
Run automated Pytest suite for Auth and Family profiles:
```bash
python -m pytest tests/test_auth_family.py -v
```

---

## 📁 Repository Structure (Week 2)
```
caretwin-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py         # Registration, Login, JWT auth
│   │       │   └── family.py       # Family member profiles CRUD
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
│   └── test_auth_family.py         # Week 2 unit tests
├── .gitignore
├── requirements.txt
└── README.md
```

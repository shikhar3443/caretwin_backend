import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_caretwin.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_register_and_login():
    # 1. Register User
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Rohan Sharma",
            "email": "rohan@example.com",
            "password": "SecurePassword123",
            "phone": "+919876543210"
        }
    )
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert reg_data["email"] == "rohan@example.com"
    assert reg_data["full_name"] == "Rohan Sharma"

    # 2. Login User
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "rohan@example.com",
            "password": "SecurePassword123"
        }
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # 3. Get User Profile (/me)
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/api/v1/auth/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "rohan@example.com"

    # 4. Check auto-created 'Self' family member
    family_response = client.get("/api/v1/family", headers=headers)
    assert family_response.status_code == 200
    members = family_response.json()
    assert len(members) == 1
    assert members[0]["name"] == "Rohan Sharma"
    assert members[0]["relationship"] == "Self"

    # 5. Add Family Member Profile (Father)
    add_father_resp = client.post(
        "/api/v1/family",
        headers=headers,
        json={
            "name": "Suresh Sharma",
            "relationship": "Father",
            "gender": "Male",
            "dob": "1965-05-12",
            "blood_group": "O+"
        }
    )
    assert add_father_resp.status_code == 201
    father_data = add_father_resp.json()
    assert father_data["name"] == "Suresh Sharma"
    assert father_data["relationship"] == "Father"

    # 6. Verify Family List has 2 members (Self + Father)
    members_updated = client.get("/api/v1/family", headers=headers).json()
    assert len(members_updated) == 2

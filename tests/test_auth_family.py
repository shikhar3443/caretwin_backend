import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_and_login():
    unique_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    # 1. Register User
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "full_name": "Rohan Sharma",
            "email": unique_email,
            "password": "SecurePassword123",
            "phone": "+919876543210"
        }
    )
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert reg_data["email"] == unique_email
    assert reg_data["full_name"] == "Rohan Sharma"

    # 2. Login User
    login_response = client.post(
        "/api/v1/auth/login",
        data={
            "username": unique_email,
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
    assert me_response.json()["email"] == unique_email

    # 4. Check auto-created 'Self' family member
    family_response = client.get("/api/v1/family", headers=headers)
    assert family_response.status_code == 200
    members = family_response.json()
    assert len(members) >= 1
    self_member = [m for m in members if m["relationship"] == "Self"][0]
    assert self_member["name"] == "Rohan Sharma"

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

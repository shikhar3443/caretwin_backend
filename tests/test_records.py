import io
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_record_locker_lifecycle():
    unique_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    # 1. Register & Login
    client.post("/api/v1/auth/register", json={
        "full_name": "Anita Verma",
        "email": unique_email,
        "password": "Password123"
    })
    login_resp = client.post("/api/v1/auth/login", data={"username": unique_email, "password": "Password123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Self profile ID
    family_members = client.get("/api/v1/family", headers=headers).json()
    self_id = family_members[0]["id"]

    # 3. Upload a sample prescription file
    file_content = b"Sample Prescription Document Content - Blood Pressure 120/80"
    file = io.BytesIO(file_content)

    upload_resp = client.post(
        "/api/v1/records/upload",
        headers=headers,
        data={
            "family_member_id": self_id,
            "title": "Apollo Clinic Visit Prescription",
            "document_type": "Prescription"
        },
        files={"file": ("prescription.pdf", file, "application/pdf")}
    )
    assert upload_resp.status_code == 201
    record_data = upload_resp.json()
    record_id = record_data["id"]
    assert record_data["title"] == "Apollo Clinic Visit Prescription"
    assert record_data["ocr_status"] == "PENDING"

    # 4. List Records
    records_list = client.get("/api/v1/records", headers=headers).json()
    assert len(records_list) >= 1

    # 5. Download Record File
    dl_resp = client.get(f"/api/v1/records/{record_id}/download", headers=headers)
    assert dl_resp.status_code == 200
    assert dl_resp.content == file_content

    # 6. Delete Record
    del_resp = client.delete(f"/api/v1/records/{record_id}", headers=headers)
    assert del_resp.status_code == 204

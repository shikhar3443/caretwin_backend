import io
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_ocr_and_timeline_pipeline():
    unique_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    # 1. Register & Login
    client.post("/api/v1/auth/register", json={
        "full_name": "Vikram Patel",
        "email": unique_email,
        "password": "Password123"
    })
    token = client.post("/api/v1/auth/login", data={"username": unique_email, "password": "Password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Self profile ID
    self_id = client.get("/api/v1/family", headers=headers).json()[0]["id"]

    # 3. Upload a document
    file_content = b"Prescription Text: BP: 140/90 mmHg, Fasting Glucose: 130 mg/dL, HbA1c: 7.2%"
    file = io.BytesIO(file_content)
    upload_resp = client.post(
        "/api/v1/records/upload",
        headers=headers,
        data={"family_member_id": self_id, "title": "Lab Report Jan 2024", "document_type": "Lab Report"},
        files={"file": ("report.pdf", file, "application/pdf")}
    )
    record_id = upload_resp.json()["id"]

    # 4. Trigger OCR Extraction (Week 4)
    ocr_resp = client.post(
        f"/api/v1/ocr/process/{record_id}",
        headers=headers,
        json={"raw_text_input": "BP: 140/90 mmHg, Fasting Glucose: 130 mg/dL, HbA1c: 7.2%"}
    )
    assert ocr_resp.status_code == 200
    extracted_fields = ocr_resp.json()["extracted_fields"]
    assert len(extracted_fields) >= 3

    # 5. Query Health Timeline (Week 5)
    timeline_resp = client.get(f"/api/v1/timeline/{self_id}", headers=headers)
    assert timeline_resp.status_code == 200
    timeline_items = timeline_resp.json()
    assert len(timeline_items) >= 3

    # 6. Query Timeline Summary Analytics
    summary_resp = client.get(f"/api/v1/timeline/{self_id}/summary", headers=headers)
    assert summary_resp.status_code == 200
    summary_data = summary_resp.json()
    assert summary_data["patient_name"] == "Vikram Patel"
    assert len(summary_data["metrics_summary"]) >= 3

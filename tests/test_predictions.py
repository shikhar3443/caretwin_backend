import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ml_mortality_prediction_flow():
    unique_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    # 1. Register & Login
    client.post("/api/v1/auth/register", json={
        "full_name": "Aarav Sharma",
        "email": unique_email,
        "password": "Password123"
    })
    token = client.post("/api/v1/auth/login", data={"username": unique_email, "password": "Password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Schema
    schema_resp = client.get("/api/v1/predictions/schema", headers=headers)
    assert schema_resp.status_code == 200
    schema_data = schema_resp.json()
    assert "labs" in schema_data
    assert "Hemoglobin" in schema_data["labs"]
    assert "Glucose" in schema_data["labs"]

    # 3. Predict Mortality Risk
    predict_payload = {
        "age": 62,
        "gender": "M",
        "admissionType": "EMERGENCY",
        "admissionLocation": "EMERGENCY ROOM",
        "insurance": "Medicare",
        "language": "ENGLISH",
        "maritalStatus": "MARRIED",
        "race": "WHITE",
        "admissionDate": "2026-11-21",
        "labs": {
            "Hemoglobin": [11.5, 11.2],
            "Creatinine": [1.3],
            "Potassium": [4.1],
            "Urea Nitrogen": [22.0],
            "Sodium": [139.0],
            "Glucose": [135.0],
            "Calcium, Total": [9.0]
        }
    }

    pred_resp = client.post("/api/v1/predictions/mortality", headers=headers, json=predict_payload)
    assert pred_resp.status_code == 200
    result_data = pred_resp.json()["result"]
    assert "probability" in result_data
    assert "riskLevel" in result_data
    assert result_data["riskLevel"] in ["lower", "elevated"]
    assert "threshold" in result_data
    assert "disclaimer" in result_data

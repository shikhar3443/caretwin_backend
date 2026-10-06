import re
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base, engine

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def _setup():
    client.post("/api/v1/auth/register", json={"email": "a@b.com", "password": "Passw0rd!", "full_name": "A"})
    tok = client.post("/api/v1/auth/login",
                      data={"username": "a@b.com", "password": "Passw0rd!"}).json()["access_token"]
    h = {"Authorization": f"Bearer {tok}"}
    member_id = client.get("/api/v1/family", headers=h).json()[0]["id"]  # default 'Self' profile
    return h, member_id


def test_qr_flow():
    h, mid = _setup()
    assert client.post(f"/api/v1/emergency/{mid}/qr", headers=h).status_code == 400  # no profile yet

    client.put(f"/api/v1/emergency/{mid}/profile", headers=h, json={
        "blood_group": "O+", "allergies": "Penicillin", "chronic_conditions": "Type 2 diabetes",
        "emergency_contact_name": "Mom", "emergency_contact_phone": "+911234567890"})

    r = client.post(f"/api/v1/emergency/{mid}/qr", headers=h).json()
    token = re.search(r"/e/(.+)$", r["emergency_url"]).group(1)

    scan = client.get(f"/api/v1/emergency/scan/{token}")          # no auth header
    assert scan.status_code == 200 and scan.json()["allergies"] == ["Penicillin"]
    assert "Penicillin" in client.get(f"/e/{token}").text

    assert len(client.get(f"/api/v1/emergency/{mid}/access-log", headers=h).json()) == 2

    # regenerate => old token dead
    client.post(f"/api/v1/emergency/{mid}/qr", headers=h)
    assert client.get(f"/api/v1/emergency/scan/{token}").status_code == 404

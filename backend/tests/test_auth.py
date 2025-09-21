from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_and_login_flow(client: TestClient) -> None:
    register_payload = {
        "email": "alice@example.com",
        "password": "secret123",
        "full_name": "Alice",
        "role": "candidate",
    }
    resp = client.post("/api/v1/auth/register", json=register_payload)
    assert resp.status_code == 201, resp.text
    login_data = {"username": "alice@example.com", "password": "secret123"}
    login_resp = client.post("/api/v1/auth/login", data=login_data)
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]
    me_resp = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "alice@example.com"

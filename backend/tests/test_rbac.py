from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_default_user_is_ordinary_user_with_read_permissions():
    response = client.get("/api/user/me")
    assert response.status_code == 200
    payload = response.json()
    assert payload["role"]["code"] == "ordinary_user"
    assert "group:read" in payload["permissions"]
    assert "analysis:create" not in payload["permissions"]


def test_site_admin_can_list_roles():
    response = client.get("/api/user/roles", headers={"X-User-Role": "site_admin"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    codes = {item["code"] for item in payload["items"]}
    assert codes == {"ordinary_user", "data_admin", "site_admin"}


def test_ordinary_user_cannot_list_roles():
    response = client.get("/api/user/roles")
    assert response.status_code == 403
    assert response.json()["detail"] == "Permission required: user:manage"


def test_data_admin_can_submit_analysis_but_ordinary_user_cannot():
    ordinary = client.post("/api/analysis", json={"wavenumber": 1715, "tolerance": 5})
    assert ordinary.status_code == 403

    data_admin = client.post(
        "/api/analysis",
        json={"wavenumber": 1715, "tolerance": 5},
        headers={"X-User-Role": "data_admin"},
    )
    assert data_admin.status_code == 200
    payload = data_admin.json()
    assert "候选证据" in payload["summary"]
    assert payload["matches"]


def test_unknown_role_is_rejected():
    response = client.get("/api/groups", headers={"X-User-Role": "ghost"})
    assert response.status_code == 401

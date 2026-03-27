import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.django_db
class TestRegister:
    def test_register_success(self, api_client):
        resp = api_client.post("/api/auth/register/", {
            "email": "new@example.com",
            "password": "StrongPass1",
            "password_confirm": "StrongPass1",
            "first_name": "New",
            "last_name": "User",
        })
        assert resp.status_code == 200
        assert "tokens" in resp.data
        assert "access" in resp.data["tokens"]

    def test_register_weak_password(self, api_client):
        resp = api_client.post("/api/auth/register/", {
            "email": "weak@example.com",
            "password": "short",
            "password_confirm": "short",
            "first_name": "A",
            "last_name": "B",
        })
        assert resp.status_code == 400


@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, user):
        resp = api_client.post("/api/auth/login/", {
            "email": "test@example.com",
            "password": "TestPass123",
        })
        assert resp.status_code == 200
        assert "tokens" in resp.data
        assert "access" in resp.data["tokens"]

    def test_login_wrong_password(self, api_client, user):
        resp = api_client.post("/api/auth/login/", {
            "email": "test@example.com",
            "password": "WrongPass1",
        })
        assert resp.status_code == 401


@pytest.mark.django_db
class TestProtectedEndpoints:
    def test_me_requires_auth(self, api_client):
        resp = api_client.get("/api/auth/me/")
        assert resp.status_code == 401

    def test_me_authenticated(self, auth_client):
        resp = auth_client.get("/api/auth/me/")
        assert resp.status_code == 200
        assert resp.data["email"] == "test@example.com"

    def test_users_list_requires_admin(self, auth_client):
        resp = auth_client.get("/api/auth/users/")
        assert resp.status_code == 403

    def test_users_list_admin_allowed(self, admin_client):
        resp = admin_client.get("/api/auth/users/")
        assert resp.status_code == 200

    def test_update_profile_other_user_forbidden(self, auth_client, admin_user):
        resp = auth_client.patch(
            f"/api/auth/update/{admin_user.pk}",
            {"first_name": "Hacked"},
        )
        assert resp.status_code == 403

    def test_logout_requires_auth(self, api_client):
        resp = api_client.post("/api/auth/logout/")
        assert resp.status_code == 401

    def test_cart_requires_auth(self, api_client):
        resp = api_client.get("/api/auth/cart/")
        assert resp.status_code == 401


@pytest.mark.django_db
class TestTokenRefresh:
    def test_refresh_token(self, api_client, user):
        login_resp = api_client.post("/api/auth/login/", {
            "email": "test@example.com",
            "password": "TestPass123",
        })
        refresh = login_resp.data["tokens"]["refresh"]
        resp = api_client.post("/api/auth/token/refresh/", {"refresh": refresh})
        assert resp.status_code == 200
        assert "access" in resp.data

    def test_invalid_refresh_token(self, api_client):
        resp = api_client.post("/api/auth/token/refresh/", {"refresh": "invalid"})
        assert resp.status_code == 401

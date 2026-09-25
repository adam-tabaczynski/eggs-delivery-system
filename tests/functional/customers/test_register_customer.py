from fastapi.testclient import TestClient

from src.main import app
from tests.generators import make_customer

client = TestClient(app)


class TestRegisterCustomer:
    def test_registers_customer(self) -> None:
        response = client.post(
            "/customers",
            json={
                "first_name": "Ada",
                "last_name": "Lovelace",
                "email": "ada@example.com",
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["first_name"] == "Ada"
        assert body["last_name"] == "Lovelace"
        assert body["email"] == "ada@example.com"
        assert isinstance(body["id"], int)
        assert "created_at" in body
        assert "updated_at" in body

    def test_duplicate_email(self) -> None:
        existing = make_customer(email="grace@example.com")

        response = client.post(
            "/customers",
            json={
                "first_name": "Grace",
                "last_name": "Hopper",
                "email": existing.email,
            },
        )
        assert response.status_code == 409
        assert response.json() == {
            "code": "email_already_registered",
            "message": "Email already registered",
        }

    def test_rejects_invalid_body(self) -> None:
        response = client.post(
            "/customers",
            json={
                "first_name": "",
                "last_name": "Lovelace",
                "email": "ada.invalid@example.com",
            },
        )
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "request_validation"
        assert body["message"] == "Request validation failed"
        assert isinstance(body["details"], list)
        assert body["details"]

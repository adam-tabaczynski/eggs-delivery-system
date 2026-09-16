from fastapi.testclient import TestClient

from src.main import app
from tests.helpers import unique_email

client = TestClient(app)


def _payload(email: str) -> dict[str, str]:
    return {
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": email,
    }


def test_register_customer() -> None:
    email = unique_email(prefix="customer")
    response = client.post("/customers", json=_payload(email))
    assert response.status_code == 201
    body = response.json()
    assert body["first_name"] == "Ada"
    assert body["last_name"] == "Lovelace"
    assert body["email"] == email
    assert isinstance(body["id"], int)
    assert "created_at" in body
    assert "updated_at" in body


def test_register_customer_duplicate_email() -> None:
    email = unique_email(prefix="customer")
    first = client.post("/customers", json=_payload(email))
    assert first.status_code == 201
    second = client.post("/customers", json=_payload(email))
    assert second.status_code == 409
    assert second.json() == {
        "code": "email_already_registered",
        "message": "Email already registered",
    }

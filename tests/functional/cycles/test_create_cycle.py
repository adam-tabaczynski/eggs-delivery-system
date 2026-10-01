from fastapi.testclient import TestClient

from src.core.clock import Clock
from src.main import app
from tests.generators import make_provider

client = TestClient(app)


class TestCreateDeliveryCycle:
    def test_creates_cycle(self) -> None:
        clock = Clock()
        provider = make_provider()

        response = client.post(
            f"/providers/{provider.id}/cycles",
            json={
                "delivery_at": clock.move_datetime_forward(days=7).isoformat(),
                "cutoff_at": clock.move_datetime_forward(days=5).isoformat(),
                "max_eggs": 48,
            },
        )
        assert response.status_code == 201
        body = response.json()
        assert body["provider_id"] == provider.id
        assert body["max_eggs"] == 48
        assert body["status"] == "open"
        assert body["allocated_eggs"] == 0
        assert isinstance(body["id"], int)
        assert "created_at" in body
        assert "updated_at" in body

    def test_unknown_provider(self) -> None:
        clock = Clock()

        response = client.post(
            "/providers/0/cycles",
            json={
                "delivery_at": clock.move_datetime_forward(days=7).isoformat(),
                "cutoff_at": clock.move_datetime_forward(days=5).isoformat(),
                "max_eggs": 48,
            },
        )
        assert response.status_code == 404
        assert response.json() == {
            "code": "provider_not_found",
            "message": "Provider not found",
        }

    def test_rejects_invalid_body(self) -> None:
        clock = Clock()
        provider = make_provider()

        response = client.post(
            f"/providers/{provider.id}/cycles",
            json={
                "delivery_at": clock.move_datetime_forward(days=7).isoformat(),
                "cutoff_at": clock.move_datetime_forward(days=5).isoformat(),
                "max_eggs": 0,
            },
        )
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "request_validation"
        assert body["message"] == "Request validation failed"
        assert isinstance(body["details"], list)
        assert body["details"]

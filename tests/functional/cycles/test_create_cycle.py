from unittest.mock import ANY

from fastapi.testclient import TestClient

from src.core.clock import Clock
from tests.generators import make_provider
from tests.helpers import json_datetime


class TestCreateDeliveryCycle:
    def test_creates_cycle(self, client: TestClient) -> None:
        clock = Clock()
        provider = make_provider()
        delivery_at = clock.move_datetime_forward(days=7)
        cutoff_at = clock.move_datetime_forward(days=5)

        response = client.post(
            f"/providers/{provider.id}/cycles",
            json={
                "delivery_at": delivery_at.isoformat(),
                "cutoff_at": cutoff_at.isoformat(),
                "max_eggs": 48,
            },
        )
        assert response.status_code == 201
        assert response.json() == {
            "id": ANY,
            "provider_id": provider.id,
            "delivery_at": json_datetime(delivery_at),
            "cutoff_at": json_datetime(cutoff_at),
            "max_eggs": 48,
            "status": "open",
            "allocated_eggs": 0,
            "created_at": ANY,
            "updated_at": ANY,
        }

    def test_unknown_provider(self, client: TestClient) -> None:
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

    def test_rejects_invalid_body(self, client: TestClient) -> None:
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

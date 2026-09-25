from fastapi.testclient import TestClient

from src.main import app
from tests.generators import make_cycle, make_provider

client = TestClient(app)


class TestUpdateDeliveryCycle:
    def test_closes_cycle(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)

        response = client.patch(
            f"/providers/{provider.id}/cycles/{cycle.id}",
            json={"status": "closed"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == cycle.id
        assert body["provider_id"] == provider.id
        assert body["status"] == "closed"

    def test_unknown_cycle(self) -> None:
        provider = make_provider()

        response = client.patch(
            f"/providers/{provider.id}/cycles/0",
            json={"status": "closed"},
        )
        assert response.status_code == 404
        assert response.json() == {
            "code": "cycle_not_found",
            "message": "Cycle not found",
        }

    def test_rejects_invalid_body(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)

        response = client.patch(
            f"/providers/{provider.id}/cycles/{cycle.id}",
            json={"status": "open"},
        )
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "request_validation"
        assert body["message"] == "Request validation failed"
        assert isinstance(body["details"], list)
        assert body["details"]

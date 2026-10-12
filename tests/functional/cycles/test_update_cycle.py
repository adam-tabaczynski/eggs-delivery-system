from unittest.mock import ANY

from fastapi.testclient import TestClient

from tests.generators import make_customer, make_cycle, make_order, make_provider
from tests.helpers import json_datetime


class TestUpdateDeliveryCycle:
    def test_closes_cycle(self, client: TestClient) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)

        response = client.patch(
            f"/providers/{provider.id}/cycles/{cycle.id}",
            json={"status": "closed"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "id": cycle.id,
            "provider_id": provider.id,
            "delivery_at": json_datetime(cycle.delivery_at),
            "cutoff_at": json_datetime(cycle.cutoff_at),
            "max_eggs": cycle.max_eggs,
            "status": "closed",
            "allocated_eggs": order.quantity,
            "created_at": json_datetime(cycle.created_at),
            "updated_at": ANY,
        }

    def test_cancels_cycle(self, client: TestClient) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        make_order(cycle_id=cycle.id, customer_id=customer.id)

        response = client.patch(
            f"/providers/{provider.id}/cycles/{cycle.id}",
            json={"status": "cancelled"},
        )
        assert response.status_code == 200
        assert response.json() == {
            "id": cycle.id,
            "provider_id": provider.id,
            "delivery_at": json_datetime(cycle.delivery_at),
            "cutoff_at": json_datetime(cycle.cutoff_at),
            "max_eggs": cycle.max_eggs,
            "status": "cancelled",
            "allocated_eggs": 0,
            "created_at": json_datetime(cycle.created_at),
            "updated_at": ANY,
        }

    def test_unknown_cycle(self, client: TestClient) -> None:
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

    def test_rejects_invalid_body(self, client: TestClient) -> None:
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

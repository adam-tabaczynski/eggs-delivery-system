from unittest.mock import ANY

from fastapi.testclient import TestClient

from tests.generators import make_customer, make_cycle, make_provider


class TestPlaceOrder:
    def test_places_order(self, client: TestClient) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()

        response = client.post(
            f"/customers/{customer.id}/orders",
            json={"cycle_id": cycle.id, "quantity": 6},
        )
        assert response.status_code == 201
        assert response.json() == {
            "id": ANY,
            "cycle_id": cycle.id,
            "customer_id": customer.id,
            "quantity": 6,
            "status": "open",
            "created_at": ANY,
            "updated_at": ANY,
        }

    def test_unknown_customer(self, client: TestClient) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)

        response = client.post(
            "/customers/0/orders",
            json={"cycle_id": cycle.id, "quantity": 6},
        )
        assert response.status_code == 404
        assert response.json() == {
            "code": "customer_not_found",
            "message": "Customer not found",
        }

    def test_rejects_invalid_body(self, client: TestClient) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()

        response = client.post(
            f"/customers/{customer.id}/orders",
            json={"cycle_id": cycle.id, "quantity": 0},
        )
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "request_validation"
        assert body["message"] == "Request validation failed"
        assert isinstance(body["details"], list)
        assert body["details"]

from fastapi.testclient import TestClient

from src.main import app
from tests.generators import make_customer, make_cycle, make_order, make_provider

client = TestClient(app)


class TestUpdateOrder:
    def test_changes_quantity(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id, quantity=6)

        response = client.patch(
            f"/customers/{customer.id}/orders/{order.id}",
            json={"quantity": 12},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == order.id
        assert body["quantity"] == 12
        assert body["status"] == "open"

    def test_soft_cancel(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id, quantity=6)

        response = client.patch(
            f"/customers/{customer.id}/orders/{order.id}",
            json={"status": "cancelled"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["id"] == order.id
        assert body["status"] == "cancelled"
        assert body["quantity"] == 6

    def test_unknown_order(self) -> None:
        customer = make_customer()

        response = client.patch(
            f"/customers/{customer.id}/orders/0",
            json={"quantity": 12},
        )
        assert response.status_code == 404
        assert response.json() == {
            "code": "order_not_found",
            "message": "Order not found",
        }

    def test_rejects_invalid_body(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)

        response = client.patch(
            f"/customers/{customer.id}/orders/{order.id}",
            json={},
        )
        assert response.status_code == 422
        body = response.json()
        assert body["code"] == "request_validation"
        assert body["message"] == "Request validation failed"
        assert isinstance(body["details"], list)
        assert body["details"]

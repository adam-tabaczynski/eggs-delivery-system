from fastapi.testclient import TestClient

from src.models import OrderStatus
from tests.generators import make_customer, make_cycle, make_order, make_provider
from tests.helpers import json_datetime


class TestListOrdersForCustomer:
    def test_lists_open_and_cancelled_orders(self, client: TestClient) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        opened = make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            quantity=12,
            status=OrderStatus.OPEN,
        )
        cancelled = make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            quantity=6,
            status=OrderStatus.CANCELLED,
        )

        response = client.get(f"/customers/{customer.id}/orders")
        assert response.status_code == 200
        assert response.json() == [
            {
                "id": opened.id,
                "cycle_id": cycle.id,
                "customer_id": customer.id,
                "quantity": 12,
                "status": "open",
                "created_at": json_datetime(opened.created_at),
                "updated_at": json_datetime(opened.updated_at),
            },
            {
                "id": cancelled.id,
                "cycle_id": cycle.id,
                "customer_id": customer.id,
                "quantity": 6,
                "status": "cancelled",
                "created_at": json_datetime(cancelled.created_at),
                "updated_at": json_datetime(cancelled.updated_at),
            },
        ]

    def test_filters_by_status(self, client: TestClient) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        make_order(cycle_id=cycle.id, customer_id=customer.id, status=OrderStatus.OPEN)
        cancelled = make_order(
            cycle_id=cycle.id,
            customer_id=customer.id,
            status=OrderStatus.CANCELLED,
        )

        response = client.get(
            f"/customers/{customer.id}/orders", params={"status": "cancelled"}
        )
        assert response.status_code == 200
        assert response.json() == [
            {
                "id": cancelled.id,
                "cycle_id": cycle.id,
                "customer_id": customer.id,
                "quantity": cancelled.quantity,
                "status": "cancelled",
                "created_at": json_datetime(cancelled.created_at),
                "updated_at": json_datetime(cancelled.updated_at),
            }
        ]

    def test_unknown_customer(self, client: TestClient) -> None:
        response = client.get("/customers/0/orders")
        assert response.status_code == 404
        assert response.json() == {
            "code": "customer_not_found",
            "message": "Customer not found",
        }

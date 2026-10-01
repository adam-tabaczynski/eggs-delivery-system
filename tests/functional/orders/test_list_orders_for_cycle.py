from fastapi.testclient import TestClient

from src.main import app
from src.models import OrderStatus
from tests.generators import make_customer, make_cycle, make_order, make_provider

client = TestClient(app)


class TestListOrdersForCycle:
    def test_lists_open_and_cancelled_orders(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        other_customer = make_customer()
        opened = make_order(cycle_id=cycle.id, customer_id=customer.id, quantity=12)
        cancelled = make_order(
            cycle_id=cycle.id,
            customer_id=other_customer.id,
            quantity=6,
            status=OrderStatus.CANCELLED,
        )

        response = client.get(f"/providers/{provider.id}/cycles/{cycle.id}/orders")
        assert response.status_code == 200
        by_id = {listed["id"]: listed for listed in response.json()}
        assert by_id.keys() == {opened.id, cancelled.id}
        assert by_id[opened.id]["customer_id"] == customer.id
        assert by_id[opened.id]["status"] == "open"
        assert by_id[opened.id]["quantity"] == 12
        assert by_id[cancelled.id]["customer_id"] == other_customer.id
        assert by_id[cancelled.id]["status"] == "cancelled"
        assert by_id[cancelled.id]["quantity"] == 6

    def test_filters_by_status(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        other_customer = make_customer()
        opened = make_order(
            cycle_id=cycle.id, customer_id=customer.id, status=OrderStatus.OPEN
        )
        make_order(
            cycle_id=cycle.id,
            customer_id=other_customer.id,
            status=OrderStatus.CANCELLED,
        )

        response = client.get(
            f"/providers/{provider.id}/cycles/{cycle.id}/orders",
            params={"status": "open"},
        )
        assert response.status_code == 200
        assert [(listed["id"], listed["status"]) for listed in response.json()] == [
            (opened.id, "open")
        ]

    def test_unknown_cycle(self) -> None:
        provider = make_provider()

        response = client.get(f"/providers/{provider.id}/cycles/0/orders")
        assert response.status_code == 404
        assert response.json() == {
            "code": "cycle_not_found",
            "message": "Cycle not found",
        }

from fastapi.testclient import TestClient

from tests.generators import make_customer, make_cycle, make_order, make_provider
from tests.helpers import json_datetime


class TestListCyclesForCustomer:
    def test_lists_cycles(self, client: TestClient) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)

        response = client.get(f"/customers/{customer.id}/cycles")
        assert response.status_code == 200
        by_id = {listed["id"]: listed for listed in response.json()}
        assert by_id[cycle.id] == {
            "id": cycle.id,
            "provider_id": provider.id,
            "delivery_at": json_datetime(cycle.delivery_at),
            "cutoff_at": json_datetime(cycle.cutoff_at),
            "max_eggs": cycle.max_eggs,
            "status": "open",
            "allocated_eggs": order.quantity,
            "created_at": json_datetime(cycle.created_at),
            "updated_at": json_datetime(cycle.updated_at),
        }

    def test_unknown_customer(self, client: TestClient) -> None:
        response = client.get("/customers/0/cycles")
        assert response.status_code == 404
        assert response.json() == {
            "code": "customer_not_found",
            "message": "Customer not found",
        }

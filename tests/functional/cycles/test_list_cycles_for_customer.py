from fastapi.testclient import TestClient

from src.main import app
from tests.generators import make_customer, make_cycle, make_order, make_provider

client = TestClient(app)


class TestListCyclesForCustomer:
    def test_lists_cycles(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)

        response = client.get(f"/customers/{customer.id}/cycles")
        assert response.status_code == 200
        by_id = {listed["id"]: listed for listed in response.json()}
        assert by_id[cycle.id]["status"] == "open"
        assert by_id[cycle.id]["max_eggs"] == cycle.max_eggs
        assert by_id[cycle.id]["allocated_eggs"] == order.quantity

    def test_unknown_customer(self) -> None:
        response = client.get("/customers/0/cycles")
        assert response.status_code == 404
        assert response.json() == {
            "code": "customer_not_found",
            "message": "Customer not found",
        }

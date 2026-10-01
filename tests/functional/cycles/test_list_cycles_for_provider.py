from fastapi.testclient import TestClient

from src.main import app
from tests.generators import make_customer, make_cycle, make_order, make_provider

client = TestClient(app)


class TestListCyclesForProvider:
    def test_lists_cycles(self) -> None:
        provider = make_provider()
        cycle = make_cycle(provider_id=provider.id)
        customer = make_customer()
        order = make_order(cycle_id=cycle.id, customer_id=customer.id)

        response = client.get(f"/providers/{provider.id}/cycles")
        assert response.status_code == 200
        cycles = response.json()
        assert [listed["id"] for listed in cycles] == [cycle.id]
        assert cycles[0]["status"] == "open"
        assert cycles[0]["max_eggs"] == cycle.max_eggs
        assert cycles[0]["allocated_eggs"] == order.quantity

    def test_unknown_provider(self) -> None:
        response = client.get("/providers/0/cycles")
        assert response.status_code == 404
        assert response.json() == {
            "code": "provider_not_found",
            "message": "Provider not found",
        }

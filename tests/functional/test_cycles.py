from fastapi.testclient import TestClient

from src.core.clock import Clock
from src.main import app
from src.models import DeliveryCycleStatus
from tests.generators import make_customer, make_cycle, make_provider

client = TestClient(app)


def test_create_cycle() -> None:
    clock = Clock()
    provider = make_provider()
    response = client.post(
        f"/providers/{provider.id}/cycles",
        json={
            "delivery_at": clock.move_datetime_forward(days=7).isoformat(),
            "cutoff_at": clock.move_datetime_forward(days=5).isoformat(),
            "max_eggs": 48,
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["provider_id"] == provider.id
    assert body["max_eggs"] == 48
    assert body["status"] == "open"
    assert isinstance(body["id"], int)
    assert "created_at" in body
    assert "updated_at" in body


def test_create_cycle_unknown_provider() -> None:
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


def test_create_cycle_rejects_non_positive_max_eggs() -> None:
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


def test_create_cycle_rejects_cutoff_after_delivery() -> None:
    clock = Clock()
    provider = make_provider()
    response = client.post(
        f"/providers/{provider.id}/cycles",
        json={
            "delivery_at": clock.move_datetime_forward(days=5).isoformat(),
            "cutoff_at": clock.move_datetime_forward(days=7).isoformat(),
            "max_eggs": 48,
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]


def test_list_cycles() -> None:
    provider = make_provider()
    cycle = make_cycle(provider_id=provider.id)

    response = client.get(f"/providers/{provider.id}/cycles")
    assert response.status_code == 200
    cycles = response.json()
    assert [listed["id"] for listed in cycles] == [cycle.id]
    assert cycles[0]["status"] == "open"


def test_list_cycles_empty() -> None:
    provider = make_provider()

    response = client.get(f"/providers/{provider.id}/cycles")
    assert response.status_code == 200
    assert response.json() == []


def test_list_cycles_unknown_provider() -> None:
    response = client.get("/providers/0/cycles")
    assert response.status_code == 404
    assert response.json() == {
        "code": "provider_not_found",
        "message": "Provider not found",
    }


def test_update_cycle() -> None:
    provider = make_provider()
    cycle = make_cycle(provider_id=provider.id)

    response = client.patch(
        f"/providers/{provider.id}/cycles/{cycle.id}",
        json={"status": "closed"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == cycle.id
    assert body["status"] == "closed"


def test_update_cycle_unknown_provider() -> None:
    provider = make_provider()
    cycle = make_cycle(provider_id=provider.id)

    response = client.patch(
        f"/providers/0/cycles/{cycle.id}",
        json={"status": "closed"},
    )
    assert response.status_code == 404
    assert response.json() == {
        "code": "provider_not_found",
        "message": "Provider not found",
    }


def test_update_cycle_unknown_cycle() -> None:
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


def test_update_cycle_already_closed() -> None:
    provider = make_provider()
    cycle = make_cycle(provider_id=provider.id, status=DeliveryCycleStatus.CLOSED)

    response = client.patch(
        f"/providers/{provider.id}/cycles/{cycle.id}",
        json={"status": "closed"},
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "cycle_already_closed",
        "message": "Cycle is already closed",
    }


def test_update_cycle_rejects_open_status() -> None:
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


def test_update_cycle_rejects_other_fields() -> None:
    provider = make_provider()
    cycle = make_cycle(provider_id=provider.id)

    response = client.patch(
        f"/providers/{provider.id}/cycles/{cycle.id}",
        json={"status": "closed", "max_eggs": 12},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]


def test_list_cycles_for_customer() -> None:
    provider = make_provider()
    cycle = make_cycle(provider_id=provider.id)
    customer = make_customer()

    response = client.get(f"/customers/{customer.id}/cycles")
    assert response.status_code == 200
    by_id = {listed["id"]: listed for listed in response.json()}
    assert by_id[cycle.id]["status"] == "open"
    assert by_id[cycle.id]["max_eggs"] == cycle.max_eggs


def test_list_cycles_for_customer_unknown_customer() -> None:
    response = client.get("/customers/0/cycles")
    assert response.status_code == 404
    assert response.json() == {
        "code": "customer_not_found",
        "message": "Customer not found",
    }

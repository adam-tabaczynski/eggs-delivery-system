from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from src.main import app
from tests.helpers import future_cycle_window, past_cycle_window

client = TestClient(app)


def _payload(**overrides: object) -> dict[str, object]:
    cutoff_at, delivery_at = future_cycle_window()
    body: dict[str, object] = {
        "delivery_at": delivery_at.isoformat(),
        "cutoff_at": cutoff_at.isoformat(),
        "max_eggs": 48,
    }
    body.update(overrides)
    return body


def _update_payload() -> dict[str, object]:
    return {"status": "closed"}


def test_create_and_list_cycles(provider_id: int) -> None:
    created = client.post(f"/providers/{provider_id}/cycles", json=_payload())
    assert created.status_code == 201
    body = created.json()
    assert body["provider_id"] == provider_id
    assert body["max_eggs"] == 48
    assert body["status"] == "open"
    assert isinstance(body["id"], int)
    assert "created_at" in body
    assert "updated_at" in body

    listed = client.get(f"/providers/{provider_id}/cycles")
    assert listed.status_code == 200
    cycles = listed.json()
    assert len(cycles) == 1
    assert cycles[0]["id"] == body["id"]


def test_list_cycles_empty(provider_id: int) -> None:
    response = client.get(f"/providers/{provider_id}/cycles")
    assert response.status_code == 200
    assert response.json() == []


def test_create_cycle_unknown_provider() -> None:
    response = client.post("/providers/0/cycles", json=_payload())
    assert response.status_code == 404
    assert response.json() == {
        "code": "provider_not_found",
        "message": "Provider not found",
    }


def test_list_cycles_unknown_provider() -> None:
    response = client.get("/providers/0/cycles")
    assert response.status_code == 404
    assert response.json() == {
        "code": "provider_not_found",
        "message": "Provider not found",
    }


def test_create_cycle_rejects_non_positive_max_eggs(provider_id: int) -> None:
    response = client.post(
        f"/providers/{provider_id}/cycles",
        json=_payload(max_eggs=0),
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]


def test_update_cycle(provider_id: int) -> None:
    created = client.post(f"/providers/{provider_id}/cycles", json=_payload())
    cycle_id = created.json()["id"]

    updated = client.patch(
        f"/providers/{provider_id}/cycles/{cycle_id}",
        json=_update_payload(),
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "closed"

    listed = client.get(f"/providers/{provider_id}/cycles")
    assert listed.json()[0]["status"] == "closed"


def test_update_cycle_unknown_provider() -> None:
    response = client.patch("/providers/0/cycles/1", json=_update_payload())
    assert response.status_code == 404
    assert response.json() == {
        "code": "provider_not_found",
        "message": "Provider not found",
    }


def test_update_cycle_unknown_cycle(provider_id: int) -> None:
    response = client.patch(
        f"/providers/{provider_id}/cycles/0",
        json=_update_payload(),
    )
    assert response.status_code == 404
    assert response.json() == {
        "code": "cycle_not_found",
        "message": "Cycle not found",
    }


def test_update_cycle_already_closed(provider_id: int) -> None:
    created = client.post(f"/providers/{provider_id}/cycles", json=_payload())
    cycle_id = created.json()["id"]
    client.patch(
        f"/providers/{provider_id}/cycles/{cycle_id}",
        json=_update_payload(),
    )

    response = client.patch(
        f"/providers/{provider_id}/cycles/{cycle_id}",
        json=_update_payload(),
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "cycle_already_closed",
        "message": "Cycle is already closed",
    }


def test_update_cycle_rejects_open_status(provider_id: int) -> None:
    created = client.post(f"/providers/{provider_id}/cycles", json=_payload())
    cycle_id = created.json()["id"]

    response = client.patch(
        f"/providers/{provider_id}/cycles/{cycle_id}",
        json={"status": "open"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]


def test_update_cycle_rejects_other_fields(provider_id: int) -> None:
    created = client.post(f"/providers/{provider_id}/cycles", json=_payload())
    cycle_id = created.json()["id"]

    response = client.patch(
        f"/providers/{provider_id}/cycles/{cycle_id}",
        json={"status": "closed", "max_eggs": 12},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]


def test_list_and_update_treat_past_cutoff_as_closed(provider_id: int) -> None:
    cutoff_at, delivery_at = past_cycle_window()
    created = client.post(
        f"/providers/{provider_id}/cycles",
        json=_payload(
            cutoff_at=cutoff_at.isoformat(),
            delivery_at=delivery_at.isoformat(),
        ),
    )
    assert created.status_code == 201
    assert created.json()["status"] == "closed"
    cycle_id = created.json()["id"]

    listed = client.get(f"/providers/{provider_id}/cycles")
    assert listed.status_code == 200
    assert listed.json()[0]["status"] == "closed"

    response = client.patch(
        f"/providers/{provider_id}/cycles/{cycle_id}",
        json=_update_payload(),
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "cycle_already_closed",
        "message": "Cycle is already closed",
    }


def test_create_cycle_rejects_cutoff_after_delivery(provider_id: int) -> None:
    now = datetime.now(UTC)
    response = client.post(
        f"/providers/{provider_id}/cycles",
        json=_payload(
            cutoff_at=(now + timedelta(days=7)).isoformat(),
            delivery_at=(now + timedelta(days=5)).isoformat(),
        ),
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]

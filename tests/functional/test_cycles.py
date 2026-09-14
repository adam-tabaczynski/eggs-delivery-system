from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from src.main import app
from tests.helpers import future_cycle_window

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
    assert response.json() == {"detail": "Provider not found"}


def test_list_cycles_unknown_provider() -> None:
    response = client.get("/providers/0/cycles")
    assert response.status_code == 404
    assert response.json() == {"detail": "Provider not found"}


def test_create_cycle_rejects_non_positive_max_eggs(provider_id: int) -> None:
    response = client.post(
        f"/providers/{provider_id}/cycles",
        json=_payload(max_eggs=0),
    )
    assert response.status_code == 422


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

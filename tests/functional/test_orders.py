from fastapi.testclient import TestClient

from src.main import app
from tests.helpers import future_cycle_window, past_cycle_window, unique_email

client = TestClient(app)


def _cycle_payload(**overrides: object) -> dict[str, object]:
    cutoff_at, delivery_at = future_cycle_window()
    body: dict[str, object] = {
        "delivery_at": delivery_at.isoformat(),
        "cutoff_at": cutoff_at.isoformat(),
        "max_eggs": 48,
    }
    body.update(overrides)
    return body


def _open_cycle(provider_id: int, **overrides: object) -> int:
    created = client.post(
        f"/providers/{provider_id}/cycles",
        json=_cycle_payload(**overrides),
    )
    assert created.status_code == 201
    return created.json()["id"]


def test_place_order(provider_id: int, customer_id: int) -> None:
    cycle_id = _open_cycle(provider_id)
    response = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["cycle_id"] == cycle_id
    assert body["customer_id"] == customer_id
    assert body["quantity"] == 6
    assert body["status"] == "open"
    assert isinstance(body["id"], int)
    assert "created_at" in body
    assert "updated_at" in body


def test_place_order_unknown_customer(provider_id: int) -> None:
    cycle_id = _open_cycle(provider_id)
    response = client.post(
        "/customers/0/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    assert response.status_code == 404
    assert response.json() == {
        "code": "customer_not_found",
        "message": "Customer not found",
    }


def test_place_order_unknown_cycle(customer_id: int) -> None:
    response = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": 0, "quantity": 6},
    )
    assert response.status_code == 404
    assert response.json() == {
        "code": "cycle_not_found",
        "message": "Cycle not found",
    }


def test_place_order_rejects_non_positive_quantity(
    provider_id: int, customer_id: int
) -> None:
    cycle_id = _open_cycle(provider_id)
    response = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 0},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]


def test_place_order_closed_cycle(provider_id: int, customer_id: int) -> None:
    cycle_id = _open_cycle(provider_id)
    client.patch(
        f"/providers/{provider_id}/cycles/{cycle_id}",
        json={"status": "closed"},
    )

    response = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "cycle_already_closed",
        "message": "Cycle is already closed",
    }


def test_place_order_after_cutoff(provider_id: int, customer_id: int) -> None:
    cutoff_at, delivery_at = past_cycle_window()
    cycle_id = _open_cycle(
        provider_id,
        cutoff_at=cutoff_at.isoformat(),
        delivery_at=delivery_at.isoformat(),
    )

    response = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "cycle_already_closed",
        "message": "Cycle is already closed",
    }


def test_update_order_quantity(provider_id: int, customer_id: int) -> None:
    cycle_id = _open_cycle(provider_id)
    placed = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    order_id = placed.json()["id"]

    response = client.patch(
        f"/customers/{customer_id}/orders/{order_id}",
        json={"quantity": 12},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["quantity"] == 12
    assert body["status"] == "open"


def test_update_order_soft_cancel(provider_id: int, customer_id: int) -> None:
    cycle_id = _open_cycle(provider_id)
    placed = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    order_id = placed.json()["id"]

    response = client.patch(
        f"/customers/{customer_id}/orders/{order_id}",
        json={"status": "cancelled"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "cancelled"
    assert body["quantity"] == 6


def test_update_order_already_cancelled(provider_id: int, customer_id: int) -> None:
    cycle_id = _open_cycle(provider_id)
    placed = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    order_id = placed.json()["id"]
    client.patch(
        f"/customers/{customer_id}/orders/{order_id}",
        json={"status": "cancelled"},
    )

    response = client.patch(
        f"/customers/{customer_id}/orders/{order_id}",
        json={"quantity": 12},
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "order_already_cancelled",
        "message": "Order is already cancelled",
    }


def test_update_order_unknown_customer(provider_id: int, customer_id: int) -> None:
    cycle_id = _open_cycle(provider_id)
    placed = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    order_id = placed.json()["id"]

    response = client.patch(
        f"/customers/0/orders/{order_id}",
        json={"quantity": 12},
    )
    assert response.status_code == 404
    assert response.json() == {
        "code": "customer_not_found",
        "message": "Customer not found",
    }


def test_update_order_unknown_order(customer_id: int) -> None:
    response = client.patch(
        f"/customers/{customer_id}/orders/0",
        json={"quantity": 12},
    )
    assert response.status_code == 404
    assert response.json() == {
        "code": "order_not_found",
        "message": "Order not found",
    }


def test_update_order_rejects_open_status(
    provider_id: int, customer_id: int
) -> None:
    cycle_id = _open_cycle(provider_id)
    placed = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    order_id = placed.json()["id"]

    response = client.patch(
        f"/customers/{customer_id}/orders/{order_id}",
        json={"status": "open"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]


def test_update_order_rejects_empty_body(
    provider_id: int, customer_id: int
) -> None:
    cycle_id = _open_cycle(provider_id)
    placed = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    order_id = placed.json()["id"]

    response = client.patch(
        f"/customers/{customer_id}/orders/{order_id}",
        json={},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]


def test_update_order_rejects_both_fields(
    provider_id: int, customer_id: int
) -> None:
    cycle_id = _open_cycle(provider_id)
    placed = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    order_id = placed.json()["id"]

    response = client.patch(
        f"/customers/{customer_id}/orders/{order_id}",
        json={"quantity": 12, "status": "cancelled"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]


def test_list_orders_empty(customer_id: int) -> None:
    response = client.get(f"/customers/{customer_id}/orders")
    assert response.status_code == 200
    assert response.json() == []


def test_list_orders_includes_open_and_cancelled(
    provider_id: int, customer_id: int
) -> None:
    cycle_id = _open_cycle(provider_id)
    placed = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    assert placed.status_code == 201
    order_id = placed.json()["id"]
    cancelled = client.patch(
        f"/customers/{customer_id}/orders/{order_id}",
        json={"status": "cancelled"},
    )
    assert cancelled.status_code == 200
    other_cycle_id = _open_cycle(provider_id)
    opened = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": other_cycle_id, "quantity": 12},
    )
    assert opened.status_code == 201

    listed = client.get(f"/customers/{customer_id}/orders")
    assert listed.status_code == 200
    orders = listed.json()
    by_id = {order["id"]: order for order in orders}
    assert by_id[order_id]["status"] == "cancelled"
    assert by_id[order_id]["quantity"] == 6
    assert by_id[opened.json()["id"]]["status"] == "open"
    assert by_id[opened.json()["id"]]["quantity"] == 12


def test_list_orders_isolates_customers(provider_id: int, customer_id: int) -> None:
    cycle_id = _open_cycle(provider_id)
    client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    other = client.post(
        "/customers",
        json={
            "first_name": "Grace",
            "last_name": "Hopper",
            "email": unique_email(prefix="customer"),
        },
    )
    assert other.status_code == 201
    other_id = other.json()["id"]
    other_order = client.post(
        f"/customers/{other_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 12},
    )
    assert other_order.status_code == 201

    listed = client.get(f"/customers/{customer_id}/orders")
    assert listed.status_code == 200
    orders = listed.json()
    assert len(orders) == 1
    assert orders[0]["customer_id"] == customer_id
    assert orders[0]["quantity"] == 6


def test_list_orders_includes_orders_after_cycle_closed(
    provider_id: int, customer_id: int
) -> None:
    cycle_id = _open_cycle(provider_id)
    placed = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    assert placed.status_code == 201
    closed = client.patch(
        f"/providers/{provider_id}/cycles/{cycle_id}",
        json={"status": "closed"},
    )
    assert closed.status_code == 200

    listed = client.get(f"/customers/{customer_id}/orders")
    assert listed.status_code == 200
    orders = listed.json()
    assert len(orders) == 1
    assert orders[0]["id"] == placed.json()["id"]
    assert orders[0]["status"] == "open"
    assert orders[0]["cycle_id"] == cycle_id


def test_list_orders_unknown_customer() -> None:
    response = client.get("/customers/0/orders")
    assert response.status_code == 404
    assert response.json() == {
        "code": "customer_not_found",
        "message": "Customer not found",
    }


def test_update_order_closed_cycle(provider_id: int, customer_id: int) -> None:
    cycle_id = _open_cycle(provider_id)
    placed = client.post(
        f"/customers/{customer_id}/orders",
        json={"cycle_id": cycle_id, "quantity": 6},
    )
    order_id = placed.json()["id"]
    client.patch(
        f"/providers/{provider_id}/cycles/{cycle_id}",
        json={"status": "closed"},
    )

    response = client.patch(
        f"/customers/{customer_id}/orders/{order_id}",
        json={"quantity": 12},
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "cycle_already_closed",
        "message": "Cycle is already closed",
    }

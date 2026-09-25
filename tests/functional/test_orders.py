from fastapi.testclient import TestClient

from src.main import app
from src.models import DeliveryCycleStatus, OrderStatus
from tests.generators import make_customer, make_cycle, make_order, make_provider

client = TestClient(app)


def test_place_order() -> None:
    cycle = make_cycle(provider_id=make_provider().id)
    customer = make_customer()

    response = client.post(
        f"/customers/{customer.id}/orders",
        json={"cycle_id": cycle.id, "quantity": 6},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["cycle_id"] == cycle.id
    assert body["customer_id"] == customer.id
    assert body["quantity"] == 6
    assert body["status"] == "open"
    assert isinstance(body["id"], int)
    assert "created_at" in body
    assert "updated_at" in body


def test_place_order_unknown_customer() -> None:
    cycle = make_cycle(provider_id=make_provider().id)

    response = client.post(
        "/customers/0/orders",
        json={"cycle_id": cycle.id, "quantity": 6},
    )
    assert response.status_code == 404
    assert response.json() == {
        "code": "customer_not_found",
        "message": "Customer not found",
    }


def test_place_order_unknown_cycle() -> None:
    customer = make_customer()

    response = client.post(
        f"/customers/{customer.id}/orders",
        json={"cycle_id": 0, "quantity": 6},
    )
    assert response.status_code == 404
    assert response.json() == {
        "code": "cycle_not_found",
        "message": "Cycle not found",
    }


def test_place_order_rejects_non_positive_quantity() -> None:
    cycle = make_cycle(provider_id=make_provider().id)
    customer = make_customer()

    response = client.post(
        f"/customers/{customer.id}/orders",
        json={"cycle_id": cycle.id, "quantity": 0},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]


def test_place_order_closed_cycle() -> None:
    cycle = make_cycle(
        provider_id=make_provider().id, status=DeliveryCycleStatus.CLOSED
    )
    customer = make_customer()

    response = client.post(
        f"/customers/{customer.id}/orders",
        json={"cycle_id": cycle.id, "quantity": 6},
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "cycle_already_closed",
        "message": "Cycle is already closed",
    }


def test_place_order_rejects_over_capacity() -> None:
    cycle = make_cycle(provider_id=make_provider().id, max_eggs=12)
    make_order(cycle_id=cycle.id, customer_id=make_customer().id, quantity=8)
    customer = make_customer()

    response = client.post(
        f"/customers/{customer.id}/orders",
        json={"cycle_id": cycle.id, "quantity": 6},
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "cycle_capacity_exceeded",
        "message": "Cycle egg capacity exceeded",
    }


def test_update_order_quantity() -> None:
    cycle = make_cycle(provider_id=make_provider().id)
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


def test_update_order_soft_cancel() -> None:
    cycle = make_cycle(provider_id=make_provider().id)
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


def test_update_order_already_cancelled() -> None:
    cycle = make_cycle(provider_id=make_provider().id)
    customer = make_customer()
    order = make_order(
        cycle_id=cycle.id, customer_id=customer.id, status=OrderStatus.CANCELLED
    )

    response = client.patch(
        f"/customers/{customer.id}/orders/{order.id}",
        json={"quantity": 12},
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "order_already_cancelled",
        "message": "Order is already cancelled",
    }


def test_update_order_unknown_customer() -> None:
    cycle = make_cycle(provider_id=make_provider().id)
    order = make_order(cycle_id=cycle.id, customer_id=make_customer().id)

    response = client.patch(
        f"/customers/0/orders/{order.id}",
        json={"quantity": 12},
    )
    assert response.status_code == 404
    assert response.json() == {
        "code": "customer_not_found",
        "message": "Customer not found",
    }


def test_update_order_unknown_order() -> None:
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


def test_update_order_closed_cycle() -> None:
    cycle = make_cycle(
        provider_id=make_provider().id, status=DeliveryCycleStatus.CLOSED
    )
    customer = make_customer()
    order = make_order(cycle_id=cycle.id, customer_id=customer.id)

    response = client.patch(
        f"/customers/{customer.id}/orders/{order.id}",
        json={"quantity": 12},
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "cycle_already_closed",
        "message": "Cycle is already closed",
    }


def test_update_order_rejects_quantity_over_capacity() -> None:
    cycle = make_cycle(provider_id=make_provider().id, max_eggs=12)
    make_order(cycle_id=cycle.id, customer_id=make_customer().id, quantity=8)
    customer = make_customer()
    order = make_order(cycle_id=cycle.id, customer_id=customer.id, quantity=2)

    response = client.patch(
        f"/customers/{customer.id}/orders/{order.id}",
        json={"quantity": 6},
    )
    assert response.status_code == 409
    assert response.json() == {
        "code": "cycle_capacity_exceeded",
        "message": "Cycle egg capacity exceeded",
    }


def test_update_order_rejects_open_status() -> None:
    cycle = make_cycle(provider_id=make_provider().id)
    customer = make_customer()
    order = make_order(cycle_id=cycle.id, customer_id=customer.id)

    response = client.patch(
        f"/customers/{customer.id}/orders/{order.id}",
        json={"status": "open"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]


def test_update_order_rejects_empty_body() -> None:
    cycle = make_cycle(provider_id=make_provider().id)
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


def test_update_order_rejects_both_fields() -> None:
    cycle = make_cycle(provider_id=make_provider().id)
    customer = make_customer()
    order = make_order(cycle_id=cycle.id, customer_id=customer.id)

    response = client.patch(
        f"/customers/{customer.id}/orders/{order.id}",
        json={"quantity": 12, "status": "cancelled"},
    )
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "request_validation"
    assert body["message"] == "Request validation failed"
    assert isinstance(body["details"], list)
    assert body["details"]


def test_list_orders() -> None:
    cycle = make_cycle(provider_id=make_provider().id)
    customer = make_customer()
    opened = make_order(cycle_id=cycle.id, customer_id=customer.id, quantity=12)
    cancelled = make_order(
        cycle_id=cycle.id,
        customer_id=customer.id,
        quantity=6,
        status=OrderStatus.CANCELLED,
    )

    response = client.get(f"/customers/{customer.id}/orders")
    assert response.status_code == 200
    by_id = {listed["id"]: listed for listed in response.json()}
    assert by_id.keys() == {opened.id, cancelled.id}
    assert by_id[opened.id]["status"] == "open"
    assert by_id[opened.id]["quantity"] == 12
    assert by_id[cancelled.id]["status"] == "cancelled"
    assert by_id[cancelled.id]["quantity"] == 6


def test_list_orders_empty() -> None:
    customer = make_customer()

    response = client.get(f"/customers/{customer.id}/orders")
    assert response.status_code == 200
    assert response.json() == []


def test_list_orders_unknown_customer() -> None:
    response = client.get("/customers/0/orders")
    assert response.status_code == 404
    assert response.json() == {
        "code": "customer_not_found",
        "message": "Customer not found",
    }

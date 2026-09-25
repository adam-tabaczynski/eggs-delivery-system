import pytest
from pydantic import ValidationError

from src.core.clock import Clock
from src.models import OrderStatus
from src.schemas import DeliveryCycleCreate, OrderUpdate


class TestDeliveryCycleCreate:
    def test_accepts_cutoff_before_delivery(self) -> None:
        clock = Clock()
        delivery_at = clock.move_datetime_forward(days=7)
        cutoff_at = clock.move_datetime_forward(days=5)

        body = DeliveryCycleCreate.model_validate(
            {"delivery_at": delivery_at, "cutoff_at": cutoff_at, "max_eggs": 48}
        )

        assert body.delivery_at == delivery_at
        assert body.cutoff_at == cutoff_at

    def test_rejects_naive_datetime(self) -> None:
        clock = Clock()
        delivery_at = clock.move_datetime_forward(days=7).replace(tzinfo=None)
        cutoff_at = clock.move_datetime_forward(days=5)

        with pytest.raises(ValidationError):
            DeliveryCycleCreate.model_validate(
                {"delivery_at": delivery_at, "cutoff_at": cutoff_at, "max_eggs": 48}
            )

    def test_rejects_cutoff_equal_to_delivery(self) -> None:
        delivery_at = Clock().move_datetime_forward(days=7)

        with pytest.raises(ValidationError):
            DeliveryCycleCreate.model_validate(
                {"delivery_at": delivery_at, "cutoff_at": delivery_at, "max_eggs": 48}
            )

    def test_rejects_cutoff_after_delivery(self) -> None:
        clock = Clock()
        delivery_at = clock.move_datetime_forward(days=5)
        cutoff_at = clock.move_datetime_forward(days=7)

        with pytest.raises(ValidationError):
            DeliveryCycleCreate.model_validate(
                {"delivery_at": delivery_at, "cutoff_at": cutoff_at, "max_eggs": 48}
            )


class TestOrderUpdate:
    def test_accepts_quantity_only(self) -> None:
        body = OrderUpdate.model_validate({"quantity": 12})

        assert body.quantity == 12
        assert body.status is None

    def test_accepts_status_only(self) -> None:
        body = OrderUpdate.model_validate({"status": "cancelled"})

        assert body.status is OrderStatus.CANCELLED
        assert body.quantity is None

    def test_rejects_empty_body(self) -> None:
        with pytest.raises(ValidationError):
            OrderUpdate.model_validate({})

    def test_rejects_both_fields(self) -> None:
        with pytest.raises(ValidationError):
            OrderUpdate.model_validate({"quantity": 12, "status": "cancelled"})

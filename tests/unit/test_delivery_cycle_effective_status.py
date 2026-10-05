from src.core.clock import Clock
from src.models import DeliveryCycle, DeliveryCycleStatus


def test_open_before_cutoff() -> None:
    clock = Clock()
    cutoff_at = clock.move_datetime_forward(days=1)
    cycle = DeliveryCycle(status=DeliveryCycleStatus.OPEN, cutoff_at=cutoff_at)

    now = clock.move_datetime_backward(cutoff_at, hours=1)

    assert cycle.effective_status(now) is DeliveryCycleStatus.OPEN


def test_closed_at_cutoff() -> None:
    cutoff_at = Clock().move_datetime_forward(days=1)
    cycle = DeliveryCycle(status=DeliveryCycleStatus.OPEN, cutoff_at=cutoff_at)

    assert cycle.effective_status(cutoff_at) is DeliveryCycleStatus.CLOSED


def test_closed_after_cutoff() -> None:
    clock = Clock()
    cutoff_at = clock.move_datetime_backward(days=1)
    cycle = DeliveryCycle(status=DeliveryCycleStatus.OPEN, cutoff_at=cutoff_at)

    assert cycle.effective_status(clock.datetime_now()) is DeliveryCycleStatus.CLOSED


def test_stored_closed_before_cutoff() -> None:
    clock = Clock()
    cutoff_at = clock.move_datetime_forward(days=1)
    cycle = DeliveryCycle(status=DeliveryCycleStatus.CLOSED, cutoff_at=cutoff_at)

    assert cycle.effective_status(clock.datetime_now()) is DeliveryCycleStatus.CLOSED


def test_stored_cancelled_after_cutoff() -> None:
    clock = Clock()
    cutoff_at = clock.move_datetime_backward(days=1)
    cycle = DeliveryCycle(status=DeliveryCycleStatus.CANCELLED, cutoff_at=cutoff_at)

    assert cycle.effective_status(clock.datetime_now()) is DeliveryCycleStatus.CANCELLED

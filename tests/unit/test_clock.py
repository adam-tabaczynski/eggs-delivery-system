from datetime import UTC, datetime, timedelta

from src.core.clock import Clock


def test_clock_datetime_now_is_utc_aware() -> None:
    now = Clock().datetime_now()

    assert now.tzinfo is not None
    assert now.utcoffset() == UTC.utcoffset(None)


def test_move_datetime_forward_and_backward() -> None:
    clock = Clock()
    instant = datetime(2026, 9, 16, 12, 0, 0, tzinfo=UTC)

    assert clock.move_datetime_forward(instant, days=2) == instant + timedelta(days=2)
    assert clock.move_datetime_backward(instant, hours=3) == instant - timedelta(hours=3)

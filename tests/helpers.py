from datetime import datetime
from uuid import uuid4

from src.core.clock import Clock


def unique_email(*, prefix: str = "test") -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def future_cycle_window() -> tuple[datetime, datetime]:
    clock = Clock()
    now = clock.datetime_now()
    return clock.move_datetime_forward(now, days=5), clock.move_datetime_forward(
        now, days=7
    )


def past_cycle_window() -> tuple[datetime, datetime]:
    clock = Clock()
    now = clock.datetime_now()
    return clock.move_datetime_backward(now, days=2), clock.move_datetime_backward(
        now, days=1
    )

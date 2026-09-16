from datetime import UTC, datetime, timedelta
from uuid import uuid4


def unique_email(*, prefix: str = "test") -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def future_cycle_window() -> tuple[datetime, datetime]:
    now = datetime.now(UTC)
    return now + timedelta(days=5), now + timedelta(days=7)


def past_cycle_window() -> tuple[datetime, datetime]:
    now = datetime.now(UTC)
    return now - timedelta(days=2), now - timedelta(days=1)

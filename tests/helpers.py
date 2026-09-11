from uuid import uuid4


def unique_email(*, prefix: str = "test") -> str:
    return f"{prefix}-{uuid4().hex}@example.com"

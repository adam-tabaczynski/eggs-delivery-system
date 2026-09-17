from datetime import UTC, datetime, timedelta


class Clock:
    def datetime_now(self) -> datetime:
        return datetime.now(UTC)

    def move_datetime_forward(
        self, dt: datetime | None = None, **kwargs: float
    ) -> datetime:
        if not dt:
            dt = self.datetime_now()
        dt = self.normalize(dt)
        return dt + timedelta(**kwargs)

    def move_datetime_backward(
        self, dt: datetime | None = None, **kwargs: float
    ) -> datetime:
        if not dt:
            dt = self.datetime_now()
        dt = self.normalize(dt)
        return dt - timedelta(**kwargs)

    def normalize(self, dt: datetime) -> datetime:
        if dt.tzinfo is None:
            raise ValueError("Input DateTime must be timezone aware")
        return dt.astimezone(UTC).replace(microsecond=0)

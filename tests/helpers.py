import threading
from collections.abc import Callable
from uuid import uuid4


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def run_concurrently[T](*calls: Callable[[], T]) -> list[T | Exception]:
    """Start all calls together on separate threads; return each result or raised exception, in call order."""
    barrier = threading.Barrier(len(calls))
    outcomes: dict[int, T | Exception] = {}

    def run(index: int, call: Callable[[], T]) -> None:
        barrier.wait()
        try:
            outcomes[index] = call()
        except Exception as exc:  # noqa: BLE001 — returned to the test to assert on
            outcomes[index] = exc

    threads = [
        threading.Thread(target=run, args=(index, call))
        for index, call in enumerate(calls)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return [outcomes[index] for index in range(len(calls))]

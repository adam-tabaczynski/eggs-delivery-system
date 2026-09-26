import pytest

from src.exceptions import CycleCapacityExceeded
from src.models import DeliveryCycle


def test_allows_filling_to_max() -> None:
    cycle = DeliveryCycle(max_eggs=10)

    cycle.ensure_capacity(committed=6, additional=4)


def test_raises_over_max() -> None:
    cycle = DeliveryCycle(max_eggs=10)

    with pytest.raises(CycleCapacityExceeded):
        cycle.ensure_capacity(committed=6, additional=5)

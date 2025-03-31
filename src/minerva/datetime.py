"""Simulation Date."""

from __future__ import annotations

from typing import Any


class SimDate:
    """Records the current year of the simulation.

    Parameters
    ----------
    year
        The current year. default 0.
    """

    __slots__ = ("year",)

    year: int
    """The current year"""

    def __init__(self, year: int = 0) -> None:
        if year >= 0:
            self.year = year
        else:
            raise ValueError("Parameter 'year' must be greater than or equal to 0.")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(year={self.year})"

    def __copy__(self) -> SimDate:
        return SimDate(year=self.year)

    def __deepcopy__(self, memo: dict[str, Any]) -> SimDate:
        return SimDate(year=self.year)

    def __str__(self) -> str:
        return str(self.year)

    def __le__(self, other: SimDate) -> bool:
        return self.year <= other.year

    def __lt__(self, other: SimDate) -> bool:
        return self.year < other.year

    def __ge__(self, other: SimDate) -> bool:
        return self.year >= other.year

    def __gt__(self, other: SimDate) -> bool:
        return self.year > other.year

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SimDate):
            raise TypeError(f"expected {type(self)} object but was {type(other)}")
        return self.year == other.year

    def __sub__(self, other: SimDate) -> int:
        return self.year - other.year

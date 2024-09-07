"""Helper classes and functions for character motives."""

from __future__ import annotations

import enum

import numpy as np
import numpy.typing as npt

from minerva.characters.components import MoneyMotive
from minerva.constants import CHARACTER_MOTIVE_MAX
from minerva.ecs import GameObject


class MotiveTypes(enum.IntEnum):
    """An enumeration of motive types."""

    MONEY = 0
    POWER = enum.auto()
    RESPECT = enum.auto()
    FAMILY = enum.auto()
    HAPPINESS = enum.auto()
    HONOR = enum.auto()
    ROMANCE = enum.auto()
    SEX = enum.auto()
    DREAD = enum.auto()


class MotiveVector:
    """A vector representing each character motive value normalized between 0 and 1.0"""

    __slots__ = ("vect",)

    vect: npt.NDArray[np.float32]

    def __init__(
        self,
        money: float = 0,
        power: float = 0,
        respect: float = 0,
        family: float = 0,
        happiness: float = 0,
        honor: float = 0,
        romance: float = 0,
        sex: float = 0,
        dread: float = 0,
    ) -> None:
        self.vect = np.array(
            [money, power, respect, family, happiness, honor, romance, sex, dread],
            dtype=np.float32,
        )

    @property
    def money(self) -> float:
        """Get the money motive value."""
        return self.vect[0]

    @property
    def power(self) -> float:
        """Get the power motive value."""
        return self.vect[1]

    @property
    def respect(self) -> float:
        """Get the money respect value."""
        return self.vect[2]

    @property
    def family(self) -> float:
        """Get the family motive value."""
        return self.vect[3]

    @property
    def happiness(self) -> float:
        """Get the happiness motive value."""
        return self.vect[4]

    @property
    def honor(self) -> float:
        """Get the honor motive value."""
        return self.vect[5]

    @property
    def romance(self) -> float:
        """Get the romance motive value."""
        return self.vect[6]

    @property
    def sex(self) -> float:
        """Get the sex motive value."""
        return self.vect[7]

    @property
    def dread(self) -> float:
        """Get the dread motive value."""
        return self.vect[8]

    @staticmethod
    def from_array(arr: npt.NDArray[np.float32]) -> MotiveVector:
        """Create a motive vector from a numpy array."""
        assert arr.shape[0] == 9, "Array is not the proper shape for motives"
        return MotiveVector(
            money=arr[0],
            power=arr[1],
            respect=arr[2],
            family=arr[3],
            happiness=arr[4],
            honor=arr[5],
            romance=arr[6],
            sex=arr[7],
            dread=arr[8],
        )


def get_character_motives(character: GameObject) -> MotiveVector:
    """Calculate the motive vector for a character."""

    return MotiveVector(
        money=character.get_component(MoneyMotive).value / CHARACTER_MOTIVE_MAX,
        power=character.get_component(MoneyMotive).value / CHARACTER_MOTIVE_MAX,
        respect=character.get_component(MoneyMotive).value / CHARACTER_MOTIVE_MAX,
        family=character.get_component(MoneyMotive).value / CHARACTER_MOTIVE_MAX,
        happiness=character.get_component(MoneyMotive).value / CHARACTER_MOTIVE_MAX,
        honor=character.get_component(MoneyMotive).value / CHARACTER_MOTIVE_MAX,
        romance=character.get_component(MoneyMotive).value / CHARACTER_MOTIVE_MAX,
        sex=character.get_component(MoneyMotive).value / CHARACTER_MOTIVE_MAX,
        dread=character.get_component(MoneyMotive).value / CHARACTER_MOTIVE_MAX,
    )

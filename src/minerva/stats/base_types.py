"""Stat System.

This module contains an implementation of stat components. Stats are things
like health, strength, dexterity, defense, attraction, etc. Stats can have modifiers
associated with them that change their final value.

The code for the stat class is based on Kryzarel's tutorial on YouTube:
https://www.youtube.com/watch?v=SH25f3cXBVc.

"""

from __future__ import annotations

import enum
import math
from abc import ABC, abstractmethod
from typing import Callable, Optional, Protocol

from minerva.ecs import Component, Entity


class StatModifierType(enum.IntEnum):
    """Specifies how the value of a StatModifier is applied in stat calculation."""

    FLAT = 100
    """Adds a constant value to the base value."""

    PERCENT = 200
    """Additively stacks percentage increases on a modified stat."""


class StatModifier:
    """Stat modifiers provide buffs and de-buffs to the value of stats."""

    __slots__ = ("value", "modifier_type")

    value: float
    modifier_type: StatModifierType

    def __init__(
        self,
        value: float,
        modifier_type: StatModifierType = StatModifierType.FLAT,
    ) -> None:
        self.value = value
        self.modifier_type = modifier_type


class IStatCalculationStrategy(Protocol):
    """Helps calculate the value of a stat."""

    @abstractmethod
    def __call__(self, stat_component: StatComponent) -> float:
        """Calculate the value of the stat."""
        raise NotImplementedError()


class StatComponent(Component, ABC):
    """A stat such as strength, opinion, or attraction.

    Parameters
    ----------
    base_value
        The value of the stat with no modifiers applied.
    bounds
        The min and max bounds for the stat.
    is_discrete
        Should the final calculated stat value be converted to an int.
    """

    __slots__ = (
        "base_value",
        # "value",
        "cached_value",
        "modifiers",
        "active_modifiers",
        "min_value",
        "max_value",
        "is_discrete",
        "listeners",
        "calculation_strategy",
    )

    base_value: float
    """The base score for this stat used by modifiers."""
    # value: float
    # """The final score of the stat clamped between the min and max values."""
    cached_value: Optional[float]
    """The value of the stat when it was last calculated."""
    modifiers: list[StatModifier]
    """Stat modifiers to use when calculating this stat."""
    active_modifiers: list[StatModifier]
    """Modifiers that are actively contributing to a stats current value."""
    min_value: Optional[float]
    """The minimum score the overall stat is clamped to."""
    max_value: Optional[float]
    """The maximum score the overall stat is clamped to."""
    is_discrete: bool
    """Should the final calculated stat value be converted to an int."""
    listeners: list[Callable[[Entity, StatComponent], None]]
    """Callbacks to execute when the value changes."""
    calculation_strategy: IStatCalculationStrategy
    """Function used to calculate the final value of the stat."""

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
        bounds: Optional[tuple[float, float]] = None,
        is_discrete: bool = False,
    ) -> None:
        super().__init__()
        self.calculation_strategy = calculation_strategy
        self.base_value = base_value
        # self.value = base_value
        self.cached_value = None
        self.modifiers = []
        self.active_modifiers = []
        self.min_value, self.max_value = bounds if bounds is not None else (None, None)
        self.is_discrete = is_discrete
        self.listeners = []

    @property
    def value(self) -> float:
        """The final score of the stat clamped between the min and max values."""
        final_value = self.calculation_strategy(self)

        if self.max_value:
            final_value = min(final_value, self.max_value)

        if self.min_value:
            final_value = max(final_value, self.min_value)

        if self.is_discrete:
            final_value = math.trunc(final_value)

        if self.cached_value != final_value:
            self.cached_value = final_value
            self.on_value_changed()

        return final_value

    def add_modifier(self, modifier: StatModifier) -> None:
        """Add a modifier to the stat."""
        self.modifiers.append(modifier)

    def remove_modifier(self, modifier: StatModifier) -> bool:
        """Remove a modifier from the stat.

        Parameters
        ----------
        modifier
            The modifier to remove.

        Returns
        -------
        bool
            True if the modifier was removed, False otherwise.
        """
        try:
            self.modifiers.remove(modifier)
            return True
        except ValueError:
            return False

    @property
    def normalized(self) -> float:
        """Get the normalized value from 0.0 to 1.0."""
        if self.min_value is not None and self.max_value is not None:
            return (self.value - self.min_value) / (self.max_value - self.min_value)

        raise ValueError("Cannot calculate normalized value of an unbound stat.")

    def on_value_changed(self) -> None:
        """Notify all change listeners."""

        for listener in self.listeners:
            listener(self.entity, self)

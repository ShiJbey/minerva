"""Settlement Generation Functions and Classes."""

import pathlib
import random
from abc import ABC, abstractmethod
from typing import Optional, Union

from minerva.ecs import Event, GameObject, World
from minerva.sim_db import SimDB
from minerva.stats.helpers import default_stat_calc_strategy
from minerva.world_map.components import PopulationHappiness, Settlement


class ISettlementFactory(ABC):
    """Interface for factories that generate settlements and settlement data."""

    @abstractmethod
    def generate_name(self) -> str:
        """Generates a settlement name."""
        raise NotImplementedError()

    @abstractmethod
    def generate_settlement(self, name: Optional[str] = None) -> GameObject:
        """Generate a settlement."""
        raise NotImplementedError()


class SettlementFactory(ISettlementFactory):
    """A factory that generates settlements and settlement data."""

    def generate_name(self) -> str:
        raise NotImplementedError()

    def generate_settlement(self, name: Optional[str] = None) -> GameObject:
        raise NotImplementedError()


class SettlementNameFactory:
    """Generates names for settlements."""

    __slots__ = ("_names", "_rng")

    _names: list[str]
    _rng: random.Random

    def __init__(self, seed: Optional[Union[str, int]] = None) -> None:
        self._names = []
        self._rng = random.Random(seed)

    def generate_name(self) -> str:
        """Generate a new settlement name."""

        if len(self._names) == 0:
            raise ValueError("No settlement names were found.")

        return self._rng.choice(self._names)

    def register_names(self, names: list[str]) -> None:
        """Add potential names to the factory."""

        for n in names:
            self._names.append(n)

    def load_names(self, filepath: Union[str, pathlib.Path]) -> None:
        """Load potential names from a text file."""

        with open(filepath, "r", encoding="utf8") as f:
            names = f.readlines()  # Each line is a different name
            names = [n.strip() for n in names]  # Strip newlines
            names = [n for n in names if n]  # Filter empty lines

        self.register_names(names)


def generate_settlement(world: World, name: str = "") -> GameObject:
    """Construct a new settlement."""

    settlement = world.gameobjects.spawn_gameobject()
    settlement_name_factory = world.resources.get_resource(SettlementNameFactory)
    name = name if name else settlement_name_factory.generate_name()
    settlement.metadata["object_type"] = "settlement"
    settlement.add_component(Settlement(name=name))
    settlement.add_component(PopulationHappiness(default_stat_calc_strategy))
    settlement.name = name

    db = world.resources.get_resource(SimDB).db

    db.execute(
        """INSERT INTO settlements (uid, name) VALUES (?, ?);""", (settlement.uid, name)
    )
    db.commit()

    world.events.dispatch_event(
        Event(event_type="settlement-added", world=world, settlement=settlement)
    )

    return settlement

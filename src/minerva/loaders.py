"""loaders.py

Functions that facilitate loading content from files.

"""

import pathlib
from typing import Union

from minerva.characters.components import Sex
from minerva.pcg.character import CharacterNameFactory
from minerva.pcg.settlement import SettlementNameFactory
from minerva.simulation import Simulation


def load_male_first_names(
    sim: Simulation,
    filepath: Union[str, pathlib.Path],
) -> None:
    """Load character masculine names from a file."""
    name_factory = sim.world.resources.get_resource(CharacterNameFactory)
    name_factory.load_first_names(Sex.MALE, filepath)


def load_female_first_names(
    sim: Simulation,
    filepath: Union[str, pathlib.Path],
) -> None:
    """Load character feminine first names from a file."""
    name_factory = sim.world.resources.get_resource(CharacterNameFactory)
    name_factory.load_first_names(Sex.FEMALE, filepath)


def load_surnames(
    sim: Simulation,
    filepath: Union[str, pathlib.Path],
) -> None:
    """Load character surnames from a file."""
    name_factory = sim.world.resources.get_resource(CharacterNameFactory)
    name_factory.load_surnames(filepath)


def load_settlement_names(
    sim: Simulation,
    filepath: Union[str, pathlib.Path],
) -> None:
    """Load settlement names from a file."""
    settlement_name_factory = sim.world.resources.get_resource(SettlementNameFactory)
    settlement_name_factory.load_names(filepath)

"""loaders.py

Functions that facilitate loading content from files.

"""

import os
import pathlib
import sys
from typing import Any, Union

import yaml
from pydantic import ValidationError

from minerva.characters.components import Sex
from minerva.pcg.character import CharacterNameFactory
from minerva.pcg.settlement import SettlementNameFactory
from minerva.simulation import Simulation
from minerva.traits.base_types import TraitDef, TraitLibrary


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


def load_traits(sim: Simulation, filepath: Union[os.PathLike[str], str, bytes]) -> None:
    """Load trait definition data from a data file.

    Parameters
    ----------
    sim
        The simulation instance to load the data into
    filepath
        The path to the data file.
    """

    with open(filepath, "r", encoding="utf8") as file:
        data: dict[str, dict[str, Any]] = yaml.safe_load(file)

    library = sim.world.resources.get_resource(TraitLibrary)

    for trait_id, params in data.items():
        try:
            library.add_definition(
                TraitDef.model_validate({"trait_id": trait_id, **params})
            )
        except ValidationError as exc:
            error_dict = exc.errors()[0]
            if error_dict["type"] == "missing":
                print(
                    f"ERROR: Missing required field '{error_dict['loc'][0]}' "
                    f"for trait type '{trait_id}' "
                    f"in '{filepath}'."
                )
                sys.exit(1)

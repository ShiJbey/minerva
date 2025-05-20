"""Japanese names for characters, families, and settlements."""

import pathlib

from minerva.ecs import World
from minerva.pcg.text_gen import load_tracery_file

_DATA_DIR = pathlib.Path(__file__).parent / "data"


def load_names(world: World) -> None:
    """Load content from the name pack."""

    load_tracery_file(
        world,
        _DATA_DIR / "female_japanese_first_names.tracery.json",
    )

    load_tracery_file(
        world,
        _DATA_DIR / "male_japanese_first_names.tracery.json",
    )

    load_tracery_file(
        world,
        _DATA_DIR / "japanese_surnames.tracery.json",
    )

    load_tracery_file(
        world,
        _DATA_DIR / "japanese_city_names.tracery.json",
    )

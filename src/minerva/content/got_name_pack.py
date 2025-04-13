"""Game of Thrones-inspired names for characters, families, and territories."""

import pathlib

from minerva.ecs import World
from minerva.pcg.text_gen import load_tracery_file

_DATA_DIR = pathlib.Path(__file__).parent / "data"


def load_names(world: World) -> None:
    """Load content from the name pack."""

    # Load name custom data
    load_tracery_file(
        world,
        _DATA_DIR / "english_first_names.tracery.json",
    )

    load_tracery_file(
        world,
        _DATA_DIR / "got_house_names.tracery.json",
    )

    load_tracery_file(
        world,
        _DATA_DIR / "got_seat_names.tracery.json",
    )

"""Japanese City Names Plugin."""

import pathlib

from minerva.ecs import World
from minerva.pcg.text_gen import load_tracery_file


def load_names(world: World) -> None:
    """Load territory names from tracery JSON files."""

    load_tracery_file(
        world, pathlib.Path(__file__).parent / "japanese_city_names.tracery.json"
    )

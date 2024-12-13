"""Text Generation.

Minerva uses a Python-port of Kate Compton's Tracery library to generate names for
characters, families, alliance, territories, and more.

"""

import json
import pathlib
from typing import Optional, Union

import tracery
import tracery.modifiers as tracery_modifiers

from minerva.ecs import Entity, World
from minerva.pcg.base_types import NameFactory


class Tracery:
    """A class that wraps a tracery grammar instance."""

    __slots__ = ("_grammar",)

    _grammar: tracery.Grammar
    """The grammar instance."""

    def __init__(self, rng_seed: Optional[Union[str, int]] = None) -> None:
        self._grammar = tracery.Grammar(
            dict[str, str](), modifiers=tracery_modifiers.base_english
        )
        if rng_seed is not None:
            self._grammar.rng.seed(rng_seed)

    def set_rng_seed(self, seed: Union[int, str]) -> None:
        """Set the seed for RNG used during rule evaluation.

        Parameters
        ----------
        seed
            An arbitrary seed value.
        """
        self._grammar.rng.seed(seed)

    def add_rules(self, rules: dict[str, list[str]]) -> None:
        """Add grammar rules.

        Parameters
        ----------
        rules
            Rule names mapped to strings or lists of string to expend to.
        """
        for rule_name, expansion in rules.items():
            self._grammar.push_rules(rule_name, expansion)

    def generate(self, start_string: str) -> str:
        """Return a string generated using the grammar rules.

        Parameters
        ----------
        start_string
            The string to expand using grammar rules.

        Returns
        -------
        str
            The final string.
        """
        return self._grammar.flatten(start_string)


class TraceryNameFactory(NameFactory):
    """A name factory that uses Tracery."""

    __slots__ = ("pattern",)

    pattern: str
    """A string pattern given to a tracery grammar."""

    def __init__(self, pattern: str) -> None:
        super().__init__()
        self.pattern = pattern

    def generate_name(self, entity: Entity) -> str:
        world = entity.world
        tracery_instance = world.get_resource(Tracery)
        return tracery_instance.generate(self.pattern)


def load_tracery_file(world: World, file_path: Union[str, pathlib.Path]) -> None:
    """Load rules from a Tracery JSON file."""
    tracery_instance = world.get_resource(Tracery)

    with open(file_path, "r", encoding="utf8") as f:
        data: dict[str, list[str]] = json.load(f)

    tracery_instance.add_rules(data)

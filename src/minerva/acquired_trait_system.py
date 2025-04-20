"""The Acquired Trait System.

Characters can gain and lose traits based on logical rules that
run at the beginning of each round (timestep).
"""

from __future__ import annotations

from typing import Iterable, Iterator

from minerva.ecs import System, World
from minerva.relationships.helpers import (
    add_relationship_trait,
    remove_relationship_trait,
)
from minerva.sim_db import SimDB
from minerva.traits.helpers import add_trait, remove_trait


class TraitRule:
    """Dynamically adds or removed a trait based on a query."""

    __slots__ = ("name", "traits_to_add", "traits_to_remove", "query")

    name: str
    """The name of the rule."""
    traits_to_add: list[str]
    """Traits to add to characters found by the query."""
    traits_to_remove: list[str]
    """Traits to remove from characters found by the query."""
    query: str
    """A drolta query to run against the SQlite database."""

    def __init__(
        self,
        name: str,
        traits_to_add: Iterable[str],
        traits_to_remove: Iterable[str],
        query: str,
    ) -> None:
        self.name = name
        self.traits_to_add = list(traits_to_add)
        self.traits_to_remove = list(traits_to_remove)
        self.query = query


class TraitRuleDatabase:
    """A collection of all trait rules used in the simulation."""

    __slots__ = ("rules",)

    rules: list[TraitRule]

    def __init__(self) -> None:
        self.rules = []

    def add_rule(self, rule: TraitRule) -> None:
        """Add a rule to the database."""
        self.rules.append(rule)

    def add_rules(self, rules: Iterable[TraitRule]) -> None:
        """Add a collection of rules to the database."""
        self.rules.extend(rules)

    def remove_rule(self, rule: TraitRule) -> None:
        """Remove a rule from the database."""
        self.rules.remove(rule)

    def iter_rules(self) -> Iterator[TraitRule]:
        """Get an iterator for the rules in the database."""
        return iter(self.rules)


class AcquiredTraitSystem(System):
    """Adds/Removes character traits at the beginning of each round (timestep)."""

    __system_group__ = "EarlyUpdateSystems"
    __update_order__ = ("last",)

    def on_update(self, world: World) -> None:
        trait_rule_db = world.get_resource(TraitRuleDatabase)
        sim_db = world.get_resource(SimDB)

        for rule in trait_rule_db.iter_rules():
            if rule.query == "":
                raise ValueError(f"TraitRule '{rule.name}' is missing a query.")

            # We assume that all the results should be tuples containing
            # a single int. Each int is the UID of a character that passed
            # the preconditions in the query.
            results: list[tuple[int, ...]] = sim_db.query_engine.query(
                rule.query, sim_db.conn
            ).fetch_all()

            for entry in results:
                character_entity = world.get_entity(entry[0])

                for trait_id in rule.traits_to_remove:
                    remove_trait(character_entity, trait_id)

                for trait_id in rule.traits_to_add:
                    add_trait(character_entity, trait_id)


class SocialInferenceRule:
    """A rule that adds/removes traits from a relationship based on a query."""

    __slots__ = ("name", "traits_to_add", "traits_to_remove", "query")

    name: str
    """The name of the rule."""
    traits_to_add: list[str]
    """Traits to add to relationships found by the query."""
    traits_to_remove: list[str]
    """Traits to remove from relationships found by the query."""
    query: str
    """A drolta query to run against the SQlite database."""

    def __init__(
        self,
        name: str,
        traits_to_add: Iterable[str],
        traits_to_remove: Iterable[str],
        query: str,
    ) -> None:
        self.name = name
        self.traits_to_add = list(traits_to_add)
        self.traits_to_remove = list(traits_to_remove)
        self.query = query


class SocialInferenceRuleDatabase:
    """A collection of all social inference rules used in the simulation."""

    __slots__ = ("rules",)

    rules: list[SocialInferenceRule]

    def __init__(self) -> None:
        self.rules = []

    def add_rule(self, rule: SocialInferenceRule) -> None:
        """Add a rule to the database."""
        self.rules.append(rule)

    def add_rules(self, rules: Iterable[SocialInferenceRule]) -> None:
        """Add a collection of rules to the database."""
        self.rules.extend(rules)

    def remove_rule(self, rule: SocialInferenceRule) -> None:
        """Remove a rule from the database."""
        self.rules.remove(rule)

    def iter_rules(self) -> Iterator[SocialInferenceRule]:
        """Get an iterator for the rules in the database."""
        return iter(self.rules)


class SocialInferenceRuleSystem(System):
    """Adds/Removes relationship traits at the beginning of each round (timestep)."""

    __system_group__ = "EarlyUpdateSystems"
    __update_order__ = ("last",)

    def on_update(self, world: World) -> None:
        social_inference_rule_db = world.get_resource(SocialInferenceRuleDatabase)
        sim_db = world.get_resource(SimDB)

        for rule in social_inference_rule_db.iter_rules():
            if rule.query == "":
                raise ValueError(
                    f"SocialInferenceRule '{rule.name}' is missing a query."
                )

            # We assume that all the results should be tuples containing
            # a single int. Each int is the UID of a character that passed
            # the preconditions in the query.
            results: list[tuple[int, ...]] = sim_db.query_engine.query(
                rule.query, sim_db.conn
            ).fetch_all()

            for entry in results:
                relationship_owner = world.get_entity(entry[0])
                relationship_target = world.get_entity(entry[1])

                for trait_id in rule.traits_to_remove:
                    remove_relationship_trait(
                        relationship_owner, relationship_target, trait_id
                    )

                for trait_id in rule.traits_to_add:
                    add_relationship_trait(
                        relationship_owner, relationship_target, trait_id
                    )

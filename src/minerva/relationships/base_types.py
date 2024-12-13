"""Relationship System Components.

The relationship system tracks feelings of one character toward another character.
Relationships are represented as independent entities. Together they form a directed
graph.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from minerva.ecs import Component, Entity
from minerva.stats.base_types import (
    IStatCalculationStrategy,
    StatComponent,
    StatModifier,
)


class Relationship(Component):
    """Tags an entity as a relationship and tracks the owner and target."""

    __slots__ = "_target", "_owner"

    _owner: Entity
    """Who owns this relationship."""
    _target: Entity
    """Who is the relationship directed toward."""

    def __init__(
        self,
        owner: Entity,
        target: Entity,
    ) -> None:
        super().__init__()
        self._owner = owner
        self._target = target

    @property
    def owner(self) -> Entity:
        """Get the owner of the relationship."""
        return self._owner

    @property
    def target(self) -> Entity:
        """Get the target of the relationship."""
        return self._target

    def __str__(self) -> str:
        return repr(self)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(owner={self.owner.name}, "
            f"target={self.target.name})"
        )


class RelationshipManager(Component):
    """Tracks all relationships associated with an entity."""

    __slots__ = (
        "incoming_relationships",
        "outgoing_relationships",
        "incoming_modifiers",
        "outgoing_modifiers",
    )

    incoming_relationships: dict[Entity, Entity]
    """Relationship owners mapped to the Relationship entities."""
    outgoing_relationships: dict[Entity, Entity]
    """Relationship targets mapped to the Relationship entities."""
    incoming_modifiers: list[RelationshipModifier]
    """Modifiers for incoming relationships."""
    outgoing_modifiers: list[RelationshipModifier]
    """Modifiers for outgoing relationships."""

    def __init__(
        self,
    ) -> None:
        super().__init__()
        self.incoming_relationships = {}
        self.outgoing_relationships = {}
        self.incoming_modifiers = []
        self.outgoing_modifiers = []


class Opinion(StatComponent):
    """Tracks a character's opinion of another."""

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (-100, 100), True)


class Attraction(StatComponent):
    """Tracks a character's romantic attraction to another."""

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (-100, 100), True)


class RelationshipModifier:
    """Conditionally modifies an entity's relationships."""

    __slots__ = (
        "precondition",
        "attraction_modifier",
        "opinion_modifier",
    )

    precondition: RelationshipPrecondition
    """Precondition to evaluate against a relationship entity."""
    attraction_modifier: Optional[StatModifier]
    """A modifier applied to the a stat."""
    opinion_modifier: Optional[StatModifier]
    """A modifier applied to the opinion stat."""

    def __init__(
        self,
        precondition: RelationshipPrecondition,
        attraction_modifier: Optional[StatModifier] = None,
        opinion_modifier: Optional[StatModifier] = None,
    ) -> None:
        self.precondition = precondition
        self.attraction_modifier = attraction_modifier
        self.opinion_modifier = opinion_modifier

    def evaluate_precondition(self, relationship: Entity) -> bool:
        """Check the preconditions against the given relationship."""
        return self.precondition.evaluate(relationship)


class RelationshipPrecondition(ABC):
    """A precondition evaluated against a relationship."""

    @staticmethod
    def not_(precondition: RelationshipPrecondition) -> RelationshipPrecondition:
        """Performs NOT on a precondition."""
        return _PreconditionNOT(precondition)

    @staticmethod
    def any(*preconditions: RelationshipPrecondition) -> RelationshipPrecondition:
        """Evaluate to true if any precondition holds."""
        return _PreconditionOR(*preconditions)

    @staticmethod
    def all(*preconditions: RelationshipPrecondition) -> RelationshipPrecondition:
        """Evaluate to true if any precondition holds."""
        return _PreconditionAND(*preconditions)

    @abstractmethod
    def evaluate(self, relationship: Entity) -> bool:
        """Check if the relationship passes the precondition."""
        raise NotImplementedError()


class _PreconditionAND(RelationshipPrecondition):
    """Logical AND for social rule preconditions."""

    __slots__ = ("preconditions",)

    preconditions: list[RelationshipPrecondition]

    def __init__(self, *preconditions: RelationshipPrecondition) -> None:
        super().__init__()
        self.preconditions = list(preconditions)

    def evaluate(self, relationship: Entity) -> bool:
        return all(p.evaluate(relationship) for p in self.preconditions)


class _PreconditionOR(RelationshipPrecondition):
    """Logical AND for social rule preconditions."""

    __slots__ = ("preconditions",)

    preconditions: list[RelationshipPrecondition]

    def __init__(self, *preconditions: RelationshipPrecondition) -> None:
        super().__init__()
        self.preconditions = list(preconditions)

    def evaluate(self, relationship: Entity) -> bool:
        return any(p.evaluate(relationship) for p in self.preconditions)


class _PreconditionNOT(RelationshipPrecondition):
    """Logical AND for social rule preconditions."""

    __slots__ = ("precondition",)

    precondition: RelationshipPrecondition

    def __init__(self, precondition: RelationshipPrecondition) -> None:
        super().__init__()
        self.precondition = precondition

    def evaluate(self, relationship: Entity) -> bool:
        return not self.precondition.evaluate(relationship)


class SocialRule:
    """A rule that modifies a relationship."""

    __slots__ = (
        "rule_id",
        "precondition",
        "opinion_modifier",
        "attraction_modifier",
    )

    rule_id: str
    precondition: RelationshipPrecondition
    opinion_modifier: Optional[StatModifier]
    attraction_modifier: Optional[StatModifier]

    def __init__(
        self,
        rule_id: str,
        precondition: RelationshipPrecondition,
        opinion_modifier: Optional[StatModifier] = None,
        attraction_modifier: Optional[StatModifier] = None,
    ) -> None:
        self.rule_id = rule_id
        self.precondition = precondition
        self.opinion_modifier = opinion_modifier
        self.attraction_modifier = attraction_modifier

    def evaluate_precondition(self, relationship: Entity) -> bool:
        """Check if a relationship passes the preconditions for this rule."""
        return self.precondition.evaluate(relationship)


class SocialRuleLibrary:
    """Collection of all social rules that modify relationships."""

    __slots__ = ("_rules",)

    _rules: dict[str, SocialRule]

    def __init__(self) -> None:
        self._rules = {}

    def add_rule(self, rule: SocialRule) -> None:
        """Add a social rule to the library."""
        self._rules[rule.rule_id] = rule

    def get_rule_by_id(self, rule_id: str) -> SocialRule:
        """Get a social rule using its ID."""
        return self._rules[rule_id]

    def iter_rules(self) -> Iterable[SocialRule]:
        """Get an iterator to the collection of rules."""
        return iter(self._rules.values())

"""Relationship System Components.

The relationship system tracks feelings of one character toward another character.
Relationships are represented as independent GameObjects. Together they form a directed
graph.

"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Optional

from minerva.ecs import Component, GameObject
from minerva.stats.base_types import (
    IStatCalculationStrategy,
    StatComponent,
    StatModifier,
)


class Relationship(Component):
    """Tags a GameObject as a relationship and tracks the owner and target."""

    __slots__ = "_target", "_owner"

    _owner: GameObject
    """Who owns this relationship."""
    _target: GameObject
    """Who is the relationship directed toward."""

    def __init__(
        self,
        owner: GameObject,
        target: GameObject,
    ) -> None:
        super().__init__()
        self._owner = owner
        self._target = target

    @property
    def owner(self) -> GameObject:
        """Get the owner of the relationship."""
        return self._owner

    @property
    def target(self) -> GameObject:
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
    """Tracks all relationships associated with a GameObject."""

    __slots__ = (
        "incoming_relationships",
        "outgoing_relationships",
        "incoming_modifiers",
        "outgoing_modifiers",
    )

    incoming_relationships: dict[GameObject, GameObject]
    """Relationship owners mapped to the Relationship GameObjects."""
    outgoing_relationships: dict[GameObject, GameObject]
    """Relationship targets mapped to the Relationship GameObjects."""
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


class Reputation(StatComponent):
    """Tracks a relationship's reputations stat."""

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (-100, 100), True)


class Romance(StatComponent):
    """Tracks a relationship's romance stat."""

    def __init__(
        self,
        calculation_strategy: IStatCalculationStrategy,
        base_value: float = 0,
    ) -> None:
        super().__init__(calculation_strategy, base_value, (-100, 100), True)


class RelationshipModifier:
    """Conditionally modifies a GameObject's relationships."""

    __slots__ = (
        "precondition",
        "romance_modifier",
        "reputation_modifier",
    )

    precondition: RelationshipPrecondition
    """Precondition to evaluate against a relationship GameObject."""
    romance_modifier: Optional[StatModifier]
    """A modifier applied to the romance stat."""
    reputation_modifier: Optional[StatModifier]
    """A modifier applied to the reputation stat."""

    def __init__(
        self,
        precondition: RelationshipPrecondition,
        romance_modifier: Optional[StatModifier] = None,
        reputation_modifier: Optional[StatModifier] = None,
    ) -> None:
        self.precondition = precondition
        self.romance_modifier = romance_modifier
        self.reputation_modifier = reputation_modifier

    def evaluate_precondition(self, relationship: GameObject) -> bool:
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
    def evaluate(self, relationship: GameObject) -> bool:
        """Check if the relationship passes the precondition."""
        raise NotImplementedError()


class _PreconditionAND(RelationshipPrecondition):
    """Logical AND for social rule preconditions."""

    __slots__ = ("preconditions",)

    preconditions: list[RelationshipPrecondition]

    def __init__(self, *preconditions: RelationshipPrecondition) -> None:
        super().__init__()
        self.preconditions = list(preconditions)

    def evaluate(self, relationship: GameObject) -> bool:
        return all(p.evaluate(relationship) for p in self.preconditions)


class _PreconditionOR(RelationshipPrecondition):
    """Logical AND for social rule preconditions."""

    __slots__ = ("preconditions",)

    preconditions: list[RelationshipPrecondition]

    def __init__(self, *preconditions: RelationshipPrecondition) -> None:
        super().__init__()
        self.preconditions = list(preconditions)

    def evaluate(self, relationship: GameObject) -> bool:
        return any(p.evaluate(relationship) for p in self.preconditions)


class _PreconditionNOT(RelationshipPrecondition):
    """Logical AND for social rule preconditions."""

    __slots__ = ("precondition",)

    precondition: RelationshipPrecondition

    def __init__(self, precondition: RelationshipPrecondition) -> None:
        super().__init__()
        self.precondition = precondition

    def evaluate(self, relationship: GameObject) -> bool:
        return not self.precondition.evaluate(relationship)


class SocialRule:
    """A rule that modifies a relationship."""

    __slots__ = (
        "rule_id",
        "precondition",
        "reputation_modifier",
        "romance_modifier",
    )

    rule_id: str
    precondition: RelationshipPrecondition
    reputation_modifier: Optional[StatModifier]
    romance_modifier: Optional[StatModifier]

    def __init__(
        self,
        rule_id: str,
        precondition: RelationshipPrecondition,
        reputation_modifier: Optional[StatModifier] = None,
        romance_modifier: Optional[StatModifier] = None,
    ) -> None:
        self.rule_id = rule_id
        self.precondition = precondition
        self.reputation_modifier = reputation_modifier
        self.romance_modifier = romance_modifier

    def evaluate_precondition(self, relationship: GameObject) -> bool:
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

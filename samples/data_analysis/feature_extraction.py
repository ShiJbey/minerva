"""Character Feature Vector Extraction."""

from abc import abstractmethod
from typing import Protocol

import numpy as np
import numpy.typing as npt

from minerva.characters.components import (
    Character,
    Dynasty,
    DynastyTracker,
    Emperor,
    FamilyRoleFlags,
    FormerFamilyHead,
    HeadOfFamily,
    Sex,
)
from minerva.characters.metric_data import CharacterMetrics
from minerva.datetime import SimDate
from minerva.ecs import Entity


class FeatureExtractorFn(Protocol):
    """Extracts a single feature from a character."""

    @abstractmethod
    def __call__(self, character: Entity) -> float:
        """Extract a single feature."""
        raise NotImplementedError


class FeatureVectorFactory:
    """Creates feature vectors from characters."""

    __slots__ = ("extractor_fns",)

    extractor_fns: list[tuple[str, FeatureExtractorFn]]

    def __init__(self) -> None:
        self.extractor_fns = []

    def add_extractor_fn(self, label: str, fn: FeatureExtractorFn) -> None:
        """Add an extractor function to the factory."""
        self.extractor_fns.append((label, fn))

    def get_vector_len(self) -> int:
        """Get the length of feature vectors"""
        return len(self.extractor_fns)

    def get_column_headers(self) -> list[str]:
        """Get the headers for data columns."""
        return [h for h, _ in self.extractor_fns]

    def create_feature_vector(self, character: Entity) -> npt.NDArray[np.float32]:
        """Extract a feature vector from the provided character."""
        feature_vector = np.zeros(self.get_vector_len(), dtype=np.float32)

        for i, (_, extractor_fn) in enumerate(self.extractor_fns):
            feature_vector[i] = extractor_fn(character)

        return feature_vector


def sex_extractor(character: Entity) -> float:
    """Extract of character is male."""
    character_component = character.get_component(Character)
    return 1 if character_component.sex == Sex.MALE else 0


def age_extractor(character: Entity) -> float:
    """Extract the character's age"""
    character_component = character.get_component(Character)
    return character_component.age


def is_family_head_extractor(character: Entity) -> float:
    """Extract if the character the head of their family"""
    return float(
        character.has_component(HeadOfFamily)
        or character.has_component(FormerFamilyHead)
    )


def influence_point_extractor(character: Entity) -> float:
    """Extract the character's influence points"""
    character_component = character.get_component(Character)
    return character_component.influence_points


def num_siblings_extractor(character: Entity) -> float:
    """Extract the character's number of siblings"""
    character_component = character.get_component(Character)
    return len(character_component.siblings)


def num_children_extractor(character: Entity) -> float:
    """Extract the character's number of children"""
    character_component = character.get_component(Character)
    return len(character_component.children)


def is_royal_family_extractor(character: Entity) -> float:
    """Extract if a character is from the royal family."""
    world = character.world
    dynasty_tracker = world.get_resource(DynastyTracker)
    current_dynasty = dynasty_tracker.current_dynasty
    character_component = character.get_component(Character)

    if current_dynasty is None:
        return 0

    if character_component.family is None:
        return 0

    if current_dynasty.get_component(Dynasty).family == character_component.family:
        return 1

    return 0


def is_current_ruler_extractor(character: Entity) -> float:
    """Extract if a character is the current ruler."""
    return 1 if character.has_component(Emperor) else 0


def is_married_extractor(character: Entity) -> float:
    """Extract the if a character is married"""
    character_component = character.get_component(Character)
    return 1 if character_component.spouse is not None else 0


def is_family_warrior_extractor(character: Entity) -> float:
    """Extract the if a character is a family warrior."""
    character_component = character.get_component(Character)
    return 1 if FamilyRoleFlags.WARRIOR in character_component.family_roles else 0


def is_family_advisor_extractor(character: Entity) -> float:
    """Extract the if a character is a family advisor."""
    character_component = character.get_component(Character)
    return 1 if FamilyRoleFlags.ADVISOR in character_component.family_roles else 0


def times_married_extractor(character: Entity) -> float:
    """."""
    return character.get_component(CharacterMetrics).data.times_married


def num_wars_extractor(character: Entity) -> float:
    """."""
    return character.get_component(CharacterMetrics).data.num_wars


def num_wars_started_extractor(character: Entity) -> float:
    """."""
    return character.get_component(CharacterMetrics).data.num_wars_started


def num_wars_won_extractor(character: Entity) -> float:
    """."""
    return character.get_component(CharacterMetrics).data.num_wars_won


def num_wars_lost_extractor(character: Entity) -> float:
    """."""
    return character.get_component(CharacterMetrics).data.num_wars_lost


def num_revolts_quelled_extractor(character: Entity) -> float:
    """."""
    return character.get_component(CharacterMetrics).data.num_revolts_quelled


def num_coups_planned_extractor(character: Entity) -> float:
    """."""
    return character.get_component(CharacterMetrics).data.num_coups_planned


def num_territories_taken_extractor(character: Entity) -> float:
    """."""
    return character.get_component(CharacterMetrics).data.num_territories_taken


def times_ruled_extractor(character: Entity) -> float:
    """."""
    return character.get_component(CharacterMetrics).data.times_as_ruler


def num_alliances_founded_extractor(character: Entity) -> float:
    """."""
    return character.get_component(CharacterMetrics).data.num_alliances_founded


def num_failed_alliance_attempts_extractor(character: Entity) -> float:
    """."""
    return character.get_component(CharacterMetrics).data.num_failed_alliance_attempts


def num_alliances_disbanded_extractor(character: Entity) -> float:
    """."""
    return character.get_component(CharacterMetrics).data.num_alliances_disbanded


def did_inherit_throne_extractor(character: Entity) -> float:
    """."""
    return float(
        character.get_component(CharacterMetrics).data.directly_inherited_throne
    )


def time_since_last_war_extractor(character: Entity) -> float:
    """."""
    current_date = character.world.get_resource(SimDate)
    last_war_date = character.get_component(
        CharacterMetrics
    ).data.date_of_last_declared_war

    if last_war_date is None:
        return -1

    return float((current_date - last_war_date).total_months)


def get_default_vector_factory() -> FeatureVectorFactory:
    """Return a preconfigured feature vector factory."""
    factory = FeatureVectorFactory()

    factory.add_extractor_fn("sex", sex_extractor)
    factory.add_extractor_fn("age", age_extractor)
    factory.add_extractor_fn("is family head?", is_family_head_extractor)
    factory.add_extractor_fn("# influence points", influence_point_extractor)
    factory.add_extractor_fn("# siblings", num_siblings_extractor)
    factory.add_extractor_fn("# children", num_children_extractor)
    factory.add_extractor_fn("is royal?", is_royal_family_extractor)
    factory.add_extractor_fn("is current ruler?", is_current_ruler_extractor)
    factory.add_extractor_fn("is married?", is_married_extractor)
    factory.add_extractor_fn("is warrior?", is_family_warrior_extractor)
    factory.add_extractor_fn("is advisor?", is_family_advisor_extractor)
    factory.add_extractor_fn("times married", times_married_extractor)
    factory.add_extractor_fn("num wars", num_wars_extractor)
    factory.add_extractor_fn("num wars started", num_wars_started_extractor)
    factory.add_extractor_fn("num wars won", num_wars_won_extractor)
    factory.add_extractor_fn("num wars lost", num_wars_lost_extractor)
    factory.add_extractor_fn("num revolts quelled", num_revolts_quelled_extractor)
    factory.add_extractor_fn("num coups planned", num_coups_planned_extractor)
    factory.add_extractor_fn("num territories taken", num_territories_taken_extractor)
    factory.add_extractor_fn("times as ruler", times_ruled_extractor)
    factory.add_extractor_fn("num alliances founded", num_alliances_founded_extractor)
    factory.add_extractor_fn(
        "num failed alliance attempts", num_failed_alliance_attempts_extractor
    )
    factory.add_extractor_fn(
        "num alliances disbanded", num_alliances_disbanded_extractor
    )
    factory.add_extractor_fn("inherited throne?", did_inherit_throne_extractor)
    # factory.add_extractor_fn("time since last war", time_since_last_war_extractor)

    return factory

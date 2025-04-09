# pylint: disable=C0302
"""Modifier functions for manipulating characters, families, etc."""

from __future__ import annotations

import logging
import math
from typing import Iterable, Optional

from minerva.actions.scheme_types import (
    AllianceScheme,
    CoupScheme,
    SchemeManager,
    WarScheme,
)
from minerva.characters.components import (
    Character,
    Diplomacy,
    Family,
    FamilyRoleFlags,
    Fertility,
    FormerFamilyHead,
    HeadOfFamily,
    Intrigue,
    Lifespan,
    LifeStage,
    Luck,
    Marriage,
    Martial,
    Prestige,
    Prowess,
    RelationType,
    Sex,
    SexualOrientation,
    Stewardship,
)
from minerva.characters.metric_data import CharacterMetrics
from minerva.config import Config
from minerva.ecs import Active, Entity
from minerva.game_action import GameAction
from minerva.game_state import GameState
from minerva.relationships.helpers import deactivate_relationships
from minerva.sim_db import SimDB
from minerva.stats.base_types import (
    StatModifier,
    add_stat_modifier,
    get_stat_base,
    get_stat_value,
    increment_stat_base,
    remove_stat_modifier,
    set_stat_base,
)
from minerva.world_map.components import Territory
from minerva.world_map.helpers import SetTerritoryControllingFamily

_logger = logging.getLogger(__name__)

# ===================================
# Stat Helper Functions
# ===================================


def get_lifespan(entity: Entity) -> int:
    """Get the lifespan for the entity."""
    return get_stat_value(entity.get_component(Lifespan))


def set_lifespan_base(entity: Entity, value: int) -> None:
    """Set the base value for an entity's life span."""
    set_stat_base(entity.get_component(Lifespan), value)


def add_lifespan_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Add a modifier to the lifespan stat."""
    add_stat_modifier(entity, entity.get_component(Lifespan), modifier)


def remove_lifespan_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Remove a modifier from the lifespan stat."""
    remove_stat_modifier(entity, entity.get_component(Lifespan), modifier)


def get_fertility(entity: Entity) -> int:
    """Get the lifespan for the entity."""
    return get_stat_value(entity.get_component(Fertility))


def increment_fertility_base(entity: Entity, value: int) -> None:
    """Increment the fertility base value by the given amount."""
    increment_stat_base(entity.get_component(Fertility), value)


def get_fertility_base(entity: Entity) -> int:
    """Set the base value for an entity's fertility."""
    return get_stat_base(entity.get_component(Fertility))


def set_fertility_base(entity: Entity, value: int) -> None:
    """Set the base value for an entity's fertility."""
    set_stat_base(entity.get_component(Fertility), value)


def add_fertility_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Add a modifier to the fertility stat."""
    add_stat_modifier(entity, entity.get_component(Fertility), modifier)


def remove_fertility_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Remove a modifier from the fertility stat."""
    remove_stat_modifier(entity, entity.get_component(Fertility), modifier)


def get_stewardship_skill(entity: Entity) -> int:
    """Get an entity's stewardship skill."""
    return get_stat_value(entity.get_component(Stewardship))


def set_stewardship_skill_base(entity: Entity, value: int) -> None:
    """Set the base value for an entity's stewardship skill."""
    set_stat_base(entity.get_component(Stewardship), value)


def add_stewardship_skill_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Add a modifier to an entity;s stewardship skill."""
    add_stat_modifier(entity, entity.get_component(Stewardship), modifier)


def remove_stewardship_skill_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Remove a modifier from an entity's stewardship skill."""
    remove_stat_modifier(entity, entity.get_component(Stewardship), modifier)


def get_martial_skill(entity: Entity) -> int:
    """Get the an entity's martial skill."""
    return get_stat_value(entity.get_component(Martial))


def set_martial_skill_base(entity: Entity, value: int) -> None:
    """Set the base value for an entity's martial skill."""
    set_stat_base(entity.get_component(Martial), value)


def add_martial_skill_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Add a modifier to an entity's martial skill."""
    add_stat_modifier(entity, entity.get_component(Martial), modifier)


def remove_martial_skill_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Remove a modifier from an entity's martial skill."""
    remove_stat_modifier(entity, entity.get_component(Martial), modifier)


def get_intrigue_skill(entity: Entity) -> int:
    """Get the an entity's intrigue skill."""
    return get_stat_value(entity.get_component(Intrigue))


def set_intrigue_skill_base(entity: Entity, value: int) -> None:
    """Set the base value for an entity's intrigue skill."""
    set_stat_base(entity.get_component(Intrigue), value)


def add_intrigue_skill_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Add a modifier to an entity's intrigue skill."""
    add_stat_modifier(entity, entity.get_component(Intrigue), modifier)


def remove_intrigue_skill_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Remove a modifier from an entity's intrigue skill."""
    remove_stat_modifier(entity, entity.get_component(Intrigue), modifier)


def get_prowess_skill(entity: Entity) -> int:
    """Get the an entity's prowess skill."""
    return get_stat_value(entity.get_component(Prowess))


def set_prowess_skill_base(entity: Entity, value: int) -> None:
    """Set the base value for an entity's prowess skill."""
    set_stat_base(entity.get_component(Prowess), value)


def add_prowess_skill_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Add a modifier to an entity's prowess skill."""
    add_stat_modifier(entity, entity.get_component(Prowess), modifier)


def remove_prowess_skill_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Remove a modifier from an entity's prowess skill."""
    remove_stat_modifier(entity, entity.get_component(Prowess), modifier)


def get_diplomacy_skill(entity: Entity) -> int:
    """Get the an entity's diplomacy skill."""
    return get_stat_value(entity.get_component(Diplomacy))


def set_diplomacy_skill_base(entity: Entity, value: int) -> None:
    """Set the base value for an entity's diplomacy skill."""
    set_stat_base(entity.get_component(Diplomacy), value)


def add_diplomacy_skill_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Add a modifier to an entity's diplomacy skill."""
    add_stat_modifier(entity, entity.get_component(Diplomacy), modifier)


def remove_diplomacy_skill_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Remove a modifier from an entity's diplomacy skill."""
    remove_stat_modifier(entity, entity.get_component(Diplomacy), modifier)


def get_luck_skill(entity: Entity) -> int:
    """Get the an entity's luck skill."""
    return get_stat_value(entity.get_component(Luck))


def set_luck_skill_base(entity: Entity, value: int) -> None:
    """Set the base value for an entity's luck skill."""
    set_stat_base(entity.get_component(Luck), value)


def add_luck_skill_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Add a modifier to an entity's luck skill."""
    add_stat_modifier(entity, entity.get_component(Luck), modifier)


def remove_luck_skill_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Remove a modifier from an entity's luck skill."""
    remove_stat_modifier(entity, entity.get_component(Luck), modifier)


def get_prestige(entity: Entity) -> int:
    """Get the an entity's prestige skill."""
    return get_stat_value(entity.get_component(Prestige))


def set_prestige_base(entity: Entity, value: int) -> None:
    """Set the base value for an entity's prestige skill."""
    set_stat_base(entity.get_component(Prestige), value)


def increment_prestige_base(entity: Entity, value: int) -> None:
    """Increment the prestige base value by the given amount."""
    increment_stat_base(entity.get_component(Prestige), value)


def add_prestige_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Add a modifier to an entity's prestige skill."""
    add_stat_modifier(entity, entity.get_component(Prestige), modifier)


def remove_prestige_modifier(entity: Entity, modifier: StatModifier) -> None:
    """Remove a modifier from an entity's prestige skill."""
    remove_stat_modifier(entity, entity.get_component(Prestige), modifier)


# ===================================
# Family Functions
# ===================================


def set_family_name(family: Entity, name: str) -> None:
    """Set the name of the given family."""
    family_component = family.get_component(Family)

    family.name = name
    family_component.name = name

    with family.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Family SET name=? WHERE uid=?;""",
            (name, family.uid),
        )


def set_family_head(family: Entity, character: Optional[Entity]) -> None:
    """Set the current head of a family."""
    world = family.world
    family_component = family.get_component(Family)

    # Do nothing if already set properly
    if family_component.head == character:
        return

    # Remove the current family head
    if family_component.head is not None:
        former_head = family_component.head
        former_head.remove_component(HeadOfFamily)
        if former_head.has_component(FormerFamilyHead):
            former_head.remove_component(FormerFamilyHead)
        former_head.add_component(FormerFamilyHead(family))
        family_component.head = None
        family_component.former_heads.add(former_head)

        with world.get_resource(SimDB) as db:
            db.execute(
                """UPDATE Family SET family_head_uid=? WHERE uid=?;""",
                (None, family),
            )

    if character is not None:
        character.add_component(HeadOfFamily(family=family))
        family_component.head = character

        with family.world.get_resource(SimDB) as db:
            db.execute(
                """UPDATE Family SET family_head_uid=? WHERE uid=?;""",
                (character.uid, family.uid),
            )


def set_character_family(character: Entity, family: Optional[Entity]) -> None:
    """Set a character's current family."""
    character_component = character.get_component(Character)

    if character_component.family == family:
        return

    if character_component.family is not None:
        unassign_family_member_from_all_roles(character_component.family, character)
        former_family = character_component.family
        family_component = former_family.get_component(Family)
        family_component.active_members.remove(character)
        family_component.former_members.add(character)
        character_component.family = None

    if family is not None:
        family_component = family.get_component(Family)
        family_component.active_members.add(character)
        character_component.family = family

    with character.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Character SET family_uid=? WHERE uid=?;""",
            (family.uid if family else None, character.uid),
        )


def set_family_home_base(family: Entity, territory: Optional[Entity]) -> None:
    """Set the home base for the given family."""
    family_component = family.get_component(Family)

    if family_component.home_base is not None:
        former_home_base = family_component.home_base
        territory_component = former_home_base.get_component(Territory)
        territory_component.families.remove(family)
        family_component.home_base = None
        with family.world.get_resource(SimDB) as db:
            db.execute(
                """UPDATE Family SET home_base_uid=NULL WHERE uid=?""", (family,)
            )

    if territory is not None:
        territory_component = territory.get_component(Territory)
        territory_component.families.append(family)
        family_component.home_base = territory
        with family.world.get_resource(SimDB) as db:
            db.execute(
                """UPDATE Family SET home_base_uid=? WHERE uid=?""",
                (territory.uid, family),
            )


class RemoveCharacterFromPlay(GameAction):
    """Remove a character from being active in the simulation."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character.world)
        self.character = character

    def on_execute(self) -> None:
        if not self.character.is_active:
            return

        character = self.character

        character_component = character.get_component(Character)

        character.deactivate()

        if character_component.heir_to:
            heir_to_character = character_component.heir_to.get_component(Character)
            if heir_to_character.is_alive:
                remove_heir(character_component.heir_to)

        if character_component.family:
            unassign_family_member_from_all_roles(character_component.family, character)
            family_component = character_component.family.get_component(Family)
            family_component.active_members.remove(character)
            family_component.former_members.add(character)

        if character_component.spouse is not None:
            end_marriage(character, character_component.spouse)

        deactivate_relationships(character)

        # Invalidate all schemes
        scheme_manager = character.get_component(SchemeManager)
        if scheme_manager.alliance_scheme:
            alliance_scheme = scheme_manager.alliance_scheme.get_component(
                AllianceScheme
            )
            if alliance_scheme.initiator == character:
                alliance_scheme.is_valid = False
            else:
                alliance_scheme.remove_character(character)

        if scheme_manager.coup_scheme:
            coup_scheme = scheme_manager.coup_scheme.get_component(CoupScheme)
            if coup_scheme.initiator == character:
                coup_scheme.is_valid = False
            else:
                coup_scheme.remove_character(character)

        if scheme_manager.war_scheme:
            war_scheme = scheme_manager.war_scheme.get_component(WarScheme)
            if war_scheme.initiator == character:
                war_scheme.is_valid = False


class RemoveFamilyFromPlay(GameAction):
    """Remove a family from being active in the simulation."""

    __slots__ = ("family",)

    def __init__(self, family: Entity) -> None:
        super().__init__(family.world)
        self.family = family

    def on_execute(self) -> None:

        if not self.family.is_active:
            return

        world = self.world
        family = self.family
        family_component = family.get_component(Family)

        with world.get_resource(SimDB) as db:
            db.execute(
                """
                UPDATE Family
                SET defunct_year=?
                WHERE uid=?;
                """,
                (world.get_resource(GameState).year, family.uid),
            )

        # Remove any remaining characters from play
        if len(family_component.active_members) != 0:
            _logger.debug(
                "%s is not empty. Removing remaining characters from play.",
                family.name_with_uid,
            )

            for member in [*family_component.active_members]:
                self.add_reaction(RemoveCharacterFromPlay(member))

        # Remove the family from play
        set_family_home_base(family, None)

        for _, (territory, _) in world.query_components((Territory, Active)):
            if territory.controlling_family == family:
                self.add_reaction(SetTerritoryControllingFamily(territory.entity, None))

        family.deactivate()

        _logger.info(
            "[%04d]: The %s family has been removed from play.",
            world.get_resource(GameState).year,
            family.name_with_uid,
        )


def set_character_birth_family(
    character: Entity,
    family: Optional[Entity],
) -> None:
    """Set the birth family of a character."""
    character_component = character.get_component(Character)

    if character_component.birth_family == family:
        return

    if character_component.birth_family is not None:
        character_component.birth_family = None

    if family is not None:
        character_component.birth_family = family

    with character.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Character SET birth_family_uid=? WHERE uid=?;""",
            (family, character),
        )


def merge_family_with(source_family: Entity, destination_family: Entity) -> None:
    """Merge a source family into a destination family."""

    # Move all members over to the new family and remove them from the old
    source_family_component = source_family.get_component(Family)
    for character in [*source_family_component.active_members]:
        set_character_family(character, destination_family)


def get_advisor_candidates(family: Entity) -> list[Entity]:
    """Get all the characters that can be assigned as advisors.

    Returns
    -------
    list[Entity]
        All potential candidates in descending order of fitness.
    """
    candidate_score_tuples: list[tuple[Entity, float]] = []

    family_component = family.get_component(Family)

    for member in family_component.active_members:
        character_component = member.get_component(Character)

        if FamilyRoleFlags.ADVISOR in character_component.family_roles:
            continue

        if character_component.life_stage < LifeStage.ADOLESCENT:
            continue

        # Characters are scored as advisors based on stewardship and diplomacy
        diplomacy = member.get_component(Diplomacy).value
        stewardship = member.get_component(Stewardship).value
        total_score = diplomacy + stewardship

        candidate_score_tuples.append((member, total_score))

    candidate_score_tuples.sort(key=lambda x: x[1], reverse=True)

    candidates = [x[0] for x in candidate_score_tuples]

    return candidates


def get_warrior_candidates(family: Entity) -> list[Entity]:
    """Get all the characters that can be assigned as warriors.

    Returns
    -------
    list[Entity]
        All potential candidates in descending order of fitness.
    """

    candidate_score_tuples: list[tuple[Entity, float]] = []

    family_component = family.get_component(Family)

    for member in family_component.active_members:
        character_component = member.get_component(Character)

        if FamilyRoleFlags.ADVISOR in character_component.family_roles:
            continue

        if character_component.life_stage < LifeStage.ADOLESCENT:
            continue

        # Characters are scored as advisors based on stewardship and diplomacy
        martial = member.get_component(Martial).value
        prowess = member.get_component(Prowess).value
        total_score = martial + prowess

        candidate_score_tuples.append((member, total_score))

    candidate_score_tuples.sort(key=lambda x: x[1], reverse=True)

    candidates = [x[0] for x in candidate_score_tuples]

    return candidates


def assign_family_member_to_roles(
    family: Entity, character: Entity, roles: FamilyRoleFlags
) -> None:
    """Assign a character to a given set of roles."""
    config = family.world.get_resource(Config)
    family_component = family.get_component(Family)
    character_component = character.get_component(Character)

    if character not in family_component.active_members:
        raise RuntimeError(
            f"Error: Cannot assign {character.name_with_uid} to any roles. "
            f"They are not a current member of the {family.name_with_uid} family."
        )

    if (
        FamilyRoleFlags.WARRIOR in roles
        and FamilyRoleFlags.WARRIOR not in character_component.family_roles
    ):
        if len(family_component.warriors) >= config.max_warriors_per_family:
            raise RuntimeError(
                "Error: Cannot assign any additional warriors to the "
                f"{family.name_with_uid} family. All slots are full."
            )

        family_component.warriors.add(character)
        character_component.family_roles |= FamilyRoleFlags.WARRIOR

        _logger.debug(
            "%s has been assigned the role of family warrior", character.name_with_uid
        )

    if (
        FamilyRoleFlags.ADVISOR in roles
        and FamilyRoleFlags.ADVISOR not in character_component.family_roles
    ):
        if len(family_component.advisors) >= config.max_advisors_per_family:
            raise RuntimeError(
                "Error: Cannot assign any additional advisors to the "
                f"{family.name_with_uid} family. All slots are full."
            )

        family_component.advisors.add(character)
        character_component.family_roles |= FamilyRoleFlags.ADVISOR

        _logger.debug(
            "%s has been assigned the role of family advisor", character.name_with_uid
        )


def unassign_family_member_from_roles(
    family: Entity, character: Entity, roles: FamilyRoleFlags
) -> None:
    """Unassign a character from a given set of roles."""

    family_component = family.get_component(Family)
    character_component = character.get_component(Character)

    if character not in family_component.active_members:
        raise RuntimeError(
            f"Error: Cannot unassign {character.name_with_uid} from any roles. "
            f"They are not a current member of the {family.name_with_uid} family."
        )

    if (
        FamilyRoleFlags.WARRIOR in roles
        and FamilyRoleFlags.WARRIOR in character_component.family_roles
    ):
        family_component.warriors.remove(character)
        character_component.family_roles ^= FamilyRoleFlags.WARRIOR

        _logger.debug(
            "%s has been removed from their role as a family warrior",
            character.name_with_uid,
        )

    if (
        FamilyRoleFlags.ADVISOR in roles
        and FamilyRoleFlags.ADVISOR in character_component.family_roles
    ):
        family_component.advisors.remove(character)
        character_component.family_roles ^= FamilyRoleFlags.ADVISOR

        _logger.debug(
            "%s has been removed from their role as a family advisor",
            character.name_with_uid,
        )


def unassign_family_member_from_all_roles(family: Entity, character: Entity) -> None:
    """Unassign a character from a given set of roles."""

    family_component = family.get_component(Family)
    character_component = character.get_component(Character)

    if character not in family_component.active_members:
        # raise RuntimeError(
        #     f"Error: Cannot unassign {character.name_with_uid} from any roles. "
        #     f"They are not a current member of the {family.name_with_uid} family."
        # )
        return

    if FamilyRoleFlags.WARRIOR in character_component.family_roles:
        family_component.warriors.remove(character)
        character_component.family_roles ^= FamilyRoleFlags.WARRIOR

    if FamilyRoleFlags.ADVISOR in character_component.family_roles:
        family_component.advisors.remove(character)
        character_component.family_roles ^= FamilyRoleFlags.ADVISOR

    _logger.debug("%s has been removed from all family roles", character.name_with_uid)


# ===================================
# Character Functions
# ===================================


def set_character_first_name(character: Entity, name: str) -> None:
    """Set a character's first name."""

    character_component = character.get_component(Character)
    character_component.first_name = name
    character.name = character_component.full_name

    with character.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Character SET first_name=? WHERE uid=?;""",
            (name, character.uid),
        )


def set_character_surname(character: Entity, name: str) -> None:
    """Set the surname of a character."""

    character_component = character.get_component(Character)
    character_component.surname = name
    character.name = character_component.full_name

    with character.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Character SET surname=? WHERE uid=?;""",
            (name, character.uid),
        )


def set_character_birth_surname(character: Entity, name: str) -> None:
    """Set the birth surname of a character."""

    character.get_component(Character).birth_surname = name

    with character.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Character SET birth_surname=? WHERE uid=?;""",
            (name, character.uid),
        )


def set_character_sex(character: Entity, sex: Sex) -> None:
    """Set the sex of a character."""

    character.get_component(Character).sex = sex

    with character.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Character SET sex=? WHERE uid=?;""",
            (sex, character.uid),
        )


def set_character_sexual_orientation(
    character: Entity, orientation: SexualOrientation
) -> None:
    """Set the sexual orientation of a character."""

    character.get_component(Character).sexual_orientation = orientation

    with character.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Character SET sexual_orientation=? WHERE uid=?;""",
            (orientation, character.uid),
        )


def set_character_life_stage(character: Entity, life_stage: LifeStage) -> None:
    """Set the life stage of a character."""

    character.get_component(Character).life_stage = life_stage

    with character.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Character SET life_stage=? WHERE uid=?;""",
            (life_stage, character.uid),
        )


def set_character_age(character: Entity, age: float) -> None:
    """Set the age of a character."""
    character_component = character.get_component(Character)

    previous_age = character_component.age
    character_component.age = age

    if math.floor(previous_age) != math.floor(age):
        with character.world.get_resource(SimDB) as db:
            db.execute(
                """UPDATE Character SET age=? WHERE uid=?;""",
                (math.floor(age), character.uid),
            )


def set_character_birth_year(character: Entity, birth_year: int) -> None:
    """Set the birth date of a character."""

    character.get_component(Character).birth_year = birth_year

    with character.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Character SET birth_year=? WHERE uid=?;""",
            (str(birth_year), character),
        )


def set_character_death_year(character: Entity, death_year: int) -> None:
    """Set the death date of a character."""

    character.get_component(Character).death_year = death_year

    with character.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Character SET death_year=? WHERE uid=?;""",
            (str(death_year), character),
        )


def set_relation(
    character_a: Entity, character_b: Entity, relation_type: RelationType
) -> None:
    """Adds a given relation type between two characters."""
    with character_a.world.get_resource(SimDB) as db:

        # Check that these characters don't already have the given relation.
        result: int = db.execute(
            """
            SELECT
                EXISTS(
                    SELECT 1
                    FROM Relation
                    WHERE character_uid=? AND target_uid=? AND relation_type=?
                )
            ;
            """,
            (character_a.uid, character_b.uid, relation_type.name),
        ).fetchone()[0]

        if result == 1:
            return

        db.execute(
            """
            INSERT INTO Relation (character_uid, target_uid, relation_type)
            VALUES (?, ?, ?);
            """,
            (character_a.uid, character_b.uid, relation_type.name),
        )


def unset_relation(
    character_a: Entity, character_b: Entity, relation_type: RelationType
) -> None:
    """Removes a given relation type between two characters."""
    with character_a.world.get_resource(SimDB) as db:
        db.execute(
            """
            DELETE FROM Relation
            WHERE character_uid=? AND target_uid=? AND relation_type=?;
            """,
            (character_a.uid, character_b.uid, relation_type.name),
        )


def get_relations(character: Entity, relation_type: RelationType) -> list[Entity]:
    """Get all characters related to the given character by the provided relation."""
    world = character.world
    db = world.get_resource(SimDB).conn

    cursor = db.cursor()

    result = cursor.execute(
        """
        SELECT target_uid
        FROM Relation
        WHERE character_uid=? AND relation_type=?;
        """,
        (character.uid, relation_type.name),
    ).fetchall()

    output = [world.get_entity(r) for (r,) in result]

    return output


def set_character_mother(character: Entity, mother: Optional[Entity]) -> None:
    """Set the mother of a character."""

    character_component = character.get_component(Character)

    if character_component.mother is not None:
        character_component.mother = None

    if mother is not None:
        character_component.mother = mother

    if mother is not None:
        set_relation(character, mother, RelationType.MOTHER)


def set_character_father(character: Entity, father: Optional[Entity]) -> None:
    """Set the father of a character."""

    character.get_component(Character).father = father

    if father is not None:
        set_relation(character, father, RelationType.FATHER)


def set_character_biological_father(
    character: Entity, father: Optional[Entity]
) -> None:
    """Set the biological father of a character."""

    character.get_component(Character).biological_father = father

    if father is not None:
        set_relation(character, father, RelationType.FATHER)


def start_marriage(character_a: Entity, character_b: Entity) -> None:
    """Set the current spouse of a character and create a new marriage."""
    world = character_a.world
    character_a_component = character_a.get_component(Character)
    character_b_component = character_b.get_component(Character)

    # Check that both characters are not married
    if character_a_component.spouse:
        raise RuntimeError(f"Error: {character_a.name_with_uid} is already married.")

    if character_b_component.spouse:
        raise RuntimeError(f"Error: {character_b.name_with_uid} is already married.")

    current_year = world.get_resource(GameState).year

    # Set the spouse references in the component data
    character_a_component.spouse = character_b
    character_b_component.spouse = character_a

    # Update the spouse IDs in the database
    set_relation(character_b, character_a, RelationType.SPOUSE)
    set_relation(character_a, character_b, RelationType.SPOUSE)

    # Create a new marriage entries into the database
    a_to_b = world.entity(
        components=[
            Marriage(character_a, character_b, current_year),
        ]
    )
    character_a_component.marriage = a_to_b

    b_to_a = world.entity(
        components=[
            Marriage(character_b, character_a, current_year),
        ]
    )
    character_b_component.marriage = b_to_a

    character_a.get_component(CharacterMetrics).data.times_married += 1
    character_b.get_component(CharacterMetrics).data.times_married += 1


def end_marriage(character_a: Entity, character_b: Entity) -> None:
    """Unset the current spouse of a character and end the marriage."""

    character_a_component = character_a.get_component(Character)
    character_b_component = character_b.get_component(Character)

    # Check that both characters are married to each other
    if character_a_component.spouse != character_b:
        raise RuntimeError(
            f"Error: {character_a.name_with_uid} is not married to"
            f" {character_b.name_with_uid}."
        )

    if character_b_component.spouse != character_a:
        raise RuntimeError(
            f"Error: {character_b.name_with_uid} is not married to"
            f" {character_a.name_with_uid}."
        )

    # Set the spouse references in the component data
    character_a_component.spouse = None
    character_b_component.spouse = None

    # Update the spouse IDs in the database
    unset_relation(character_b, character_a, RelationType.SPOUSE)
    unset_relation(character_a, character_b, RelationType.SPOUSE)
    unset_relation(character_b, character_a, RelationType.EX_SPOUSE)
    unset_relation(character_a, character_b, RelationType.EX_SPOUSE)

    # Update marriage entries in the database
    assert character_a_component.marriage
    character_a_component.marriage = None

    assert character_b_component.marriage
    character_b_component.marriage = None


def set_character_alive(character: Entity, is_alive: bool) -> None:
    """Set is_alive status of a character."""

    character.get_component(Character).is_alive = is_alive

    with character.world.get_resource(SimDB) as db:
        db.execute(
            """UPDATE Character SET is_alive=? WHERE uid=?;""",
            (is_alive, character.uid),
        )


def set_relation_sibling(character: Entity, sibling: Entity) -> None:
    """Set a character as being a sibling to the first.

    Parameters
    ----------
    character
        The character to modify.
    sibling
        The character to set as the sibling.
    """

    character_siblings = character.get_component(Character).siblings

    if sibling not in character_siblings:
        character_siblings.append(sibling)

        set_relation(character, sibling, RelationType.SIBLING)


def set_relation_child(character: Entity, child: Entity) -> None:
    """Set a character as being a child to the first."""

    character.get_component(Character).children.append(child)

    set_relation(character, child, RelationType.CHILD)


def update_grandparent_relations(
    child: Entity, grandparents: Iterable[Optional[Entity]]
) -> None:
    """Update child's grandparent references and grandparent's grandchild references.

    Parameters
    ----------
    child
        The child to update.
    grandparents
        The child's grandparents.
    """

    child_character_component = child.get_component(Character)

    for grandparent in grandparents:
        if grandparent is None:
            continue

        grandparent_character_component = grandparent.get_component(Character)

        child_character_component.grandparents.add(grandparent)
        grandparent_character_component.grandchildren.add(child)

        set_relation(child, grandparent, RelationType.GRANDPARENT)
        set_relation(grandparent, child, RelationType.GRANDCHILD)


def get_family_of(character: Entity) -> Entity:
    """Get the family a character belongs to."""
    character_component = character.get_component(Character)

    if character_component.family is not None:
        return character_component.family

    raise TypeError(f"{character.name_with_uid} is missing a family.")


def set_heir(character: Entity, heir: Entity) -> None:
    """Set a character's heir."""
    character_component = character.get_component(Character)
    heir_character = heir.get_component(Character)

    if character_component.heir is not None:
        raise TypeError("Character already has a heir declared.")

    character_component.heir = heir
    heir_character.heir_to = character

    set_relation(character, heir, RelationType.HEIR)
    set_relation(heir, character, RelationType.HEIR_TO)


def remove_heir(character: Entity) -> None:
    """Remove the declared heir from this character."""

    character_component = character.get_component(Character)

    if character_component.heir is None:
        return

    heir = character_component.heir
    heir_character = heir.get_component(Character)

    character_component.heir = None
    heir_character.heir_to = None

    set_relation(character, heir, RelationType.HEIR)
    set_relation(heir, character, RelationType.HEIR_TO)

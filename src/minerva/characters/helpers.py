# pylint: disable=C0302
"""Modifier functions for manipulating characters, families, etc."""

from __future__ import annotations

import logging
import math
from typing import Iterable, Optional

from minerva.actions.base_types import Scheme, SchemeManager
from minerva.actions.scheme_helpers import remove_member_from_scheme
from minerva.characters.components import (
    Character,
    Diplomacy,
    RelationType,
    Ruler,
    Family,
    FamilyRoleFlags,
    FormerFamilyHead,
    HeadOfFamily,
    LifeStage,
    Marriage,
    Martial,
    Prowess,
    RomanticAffair,
    Sex,
    SexualOrientation,
    Stewardship,
    Betrothal,
)
from minerva.characters.metric_data import CharacterMetrics
from minerva.characters.succession_helpers import (
    remove_current_ruler,
)
from minerva.characters.war_helpers import end_alliance
from minerva.config import Config
from minerva.datetime import SimDate
from minerva.ecs import Active, Entity
from minerva.relationships.helpers import deactivate_relationships
from minerva.sim_db import SimDB
from minerva.world_map.components import Territory
from minerva.world_map.helpers import set_territory_controlling_family

_logger = logging.getLogger(__name__)


# ===================================
# Family Functions
# ===================================


def set_family_name(
    family: Entity,
    name: str,
) -> None:
    """Set the name of the given family."""
    family_component = family.get_component(Family)

    family.name = name
    family_component.name = name

    db = family.world.get_resource(SimDB).db
    cur = db.cursor()
    cur.execute(
        """UPDATE families SET name=? WHERE uid=?;""",
        (name, family),
    )
    db.commit()


def add_branch_family(family: Entity, branch_family: Entity) -> None:
    """Set the parent family of a family."""

    branch_family_component = branch_family.get_component(Family)
    family_component = family.get_component(Family)

    branch_family_component.parent_family = family
    family_component.branch_families.add(branch_family)

    world = branch_family.world
    db = world.get_resource(SimDB).db
    cursor = db.cursor()

    cursor.execute(
        """UPDATE families SET parent_id=? WHERE uid=?;""",
        (family.uid, branch_family.uid),
    )

    db.commit()


def set_family_head(
    family: Entity,
    character: Optional[Entity],
) -> None:
    """Set the current head of a family."""
    current_date = family.world.get_resource(SimDate).to_iso_str()
    db = family.world.get_resource(SimDB).db
    cur = db.cursor()
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
        cur.execute(
            """UPDATE family_heads SET end_date=? WHERE head=?;""",
            (current_date, former_head.uid),
        )

    # Set the new family head
    if character is not None:
        character.add_component(HeadOfFamily(family=family))
        family_component.head = character
        previous_head = (
            family_component.former_heads[-1] if family_component.former_heads else None
        )
        cur.execute(
            """
            INSERT INTO family_heads
            (head, family, start_date, predecessor)
            VALUES (?, ?, ?, ?);
            """,
            (character, family, current_date, previous_head),
        )

    cur.execute(
        """UPDATE families SET head=? WHERE uid=?;""",
        (character, family),
    )

    db.commit()


def set_character_family(
    character: Entity,
    family: Optional[Entity],
) -> None:
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

    db = character.world.get_resource(SimDB).db
    cur = db.cursor()
    cur.execute(
        """UPDATE characters SET family=? WHERE uid=?;""",
        (family, character),
    )
    db.commit()


def set_family_home_base(family: Entity, territory: Optional[Entity]) -> None:
    """Set the home base for the given family."""
    family_component = family.get_component(Family)

    db = family.world.get_resource(SimDB).db
    cur = db.cursor()

    if family_component.home_base is not None:
        former_home_base = family_component.home_base
        territory_component = former_home_base.get_component(Territory)
        territory_component.families.remove(family)
        family_component.home_base = None
        cur.execute("""UPDATE families SET home_base_id=NULL WHERE uid=?""", (family,))
        if family in territory_component.political_influence:
            del territory_component.political_influence[family]

    if territory is not None:
        territory_component = territory.get_component(Territory)
        territory_component.families.append(family)
        family_component.home_base = territory
        cur.execute(
            """UPDATE families SET home_base_id=? WHERE uid=?""",
            (territory.uid, family),
        )
        if family not in territory_component.political_influence:
            territory_component.political_influence[family] = 0

    db.commit()


def remove_family_from_play(family: Entity) -> None:
    """Remove a family from play."""
    world = family.world
    family_component = family.get_component(Family)

    db = world.get_resource(SimDB).db
    current_date = world.get_resource(SimDate)
    db_cursor = db.cursor()
    db_cursor.execute(
        """
        UPDATE families
        SET defunct_date=?
        WHERE uid=?;
        """,
        (current_date.to_iso_str(), family.uid),
    )
    db.commit()

    # Remove any remaining characters from play
    if len(family_component.active_members) != 0:
        _logger.debug(
            "%s is not empty. Removing remaining characters from play.",
            family.name_with_uid,
        )

        for member in [*family_component.active_members]:
            remove_character_from_play(member)

    # Remove the family from play
    set_family_home_base(family, None)

    for _, (territory, _) in world.query_components((Territory, Active)):
        if family in territory.political_influence:
            del territory.political_influence[family]

        if territory.controlling_family == family:
            set_territory_controlling_family(territory.entity, None)

    family.deactivate()

    # Remove family from their alliance and disband it
    if family_component.alliance:
        end_alliance(family_component.alliance)

    _logger.info(
        "[%s]: The %s family has been removed from play.",
        str(current_date),
        family.name_with_uid,
    )


def remove_character_from_play(character: Entity) -> None:
    """Remove a character from play."""
    world = character.world
    current_date = world.get_resource(SimDate).copy()
    character_component = character.get_component(Character)

    character.deactivate()

    if character_component.heir_to:
        heir_to_character = character_component.heir_to.get_component(Character)
        if heir_to_character.is_alive:
            remove_heir(character_component.heir_to)

    # Remove the character from head of their family if applicable
    if character.has_component(HeadOfFamily):
        family_head_component = character.get_component(HeadOfFamily)
        family = family_head_component.family
        set_family_head(family, None)

    if character.has_component(Ruler):
        remove_current_ruler(world)

    if character_component.family:
        unassign_family_member_from_all_roles(character_component.family, character)
        family_component = character_component.family.get_component(Family)
        family_component.active_members.remove(character)
        family_component.former_members.add(character)

    set_character_death_date(character, current_date)

    if character_component.spouse is not None:
        end_marriage(character, character_component.spouse)

    deactivate_relationships(character)

    # Invalidate all schemes
    scheme_manager = character.get_component(SchemeManager)
    for scheme in [*scheme_manager.get_schemes()]:
        scheme_component = scheme.get_component(Scheme)

        if scheme_component.initiator == character:
            scheme_component.is_valid = False

        remove_member_from_scheme(scheme, character)


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

    db = character.world.get_resource(SimDB).db
    cur = db.cursor()
    cur.execute(
        """UPDATE characters SET birth_family=? WHERE uid=?;""",
        (family, character),
    )
    db.commit()


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
        raise RuntimeError(
            f"Error: Cannot unassign {character.name_with_uid} from any roles. "
            f"They are not a current member of the {family.name_with_uid} family."
        )

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

    db = character.world.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET first_name=? WHERE uid=?;""",
        (name, character.uid),
    )

    db.commit()


def set_character_surname(character: Entity, name: str) -> None:
    """Set the surname of a character."""

    character_component = character.get_component(Character)
    character_component.surname = name
    character.name = character_component.full_name

    db = character.world.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET surname=? WHERE uid=?;""",
        (name, character.uid),
    )

    db.commit()


def set_character_birth_surname(character: Entity, name: str) -> None:
    """Set the birth surname of a character."""

    character.get_component(Character).birth_surname = name

    db = character.world.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET birth_surname=? WHERE uid=?;""",
        (name, character.uid),
    )

    db.commit()


def set_character_sex(character: Entity, sex: Sex) -> None:
    """Set the sex of a character."""

    character.get_component(Character).sex = sex

    db = character.world.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET sex=? WHERE uid=?;""",
        (sex, character.uid),
    )

    db.commit()


def set_character_sexual_orientation(
    character: Entity, orientation: SexualOrientation
) -> None:
    """Set the sexual orientation of a character."""

    character.get_component(Character).sexual_orientation = orientation

    db = character.world.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET sexual_orientation=? WHERE uid=?;""",
        (orientation, character.uid),
    )

    db.commit()


def set_character_life_stage(character: Entity, life_stage: LifeStage) -> None:
    """Set the life stage of a character."""

    character.get_component(Character).life_stage = life_stage

    db = character.world.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET life_stage=? WHERE uid=?;""",
        (life_stage, character.uid),
    )

    db.commit()


def set_character_age(character: Entity, age: float) -> None:
    """Set the age of a character."""
    character_component = character.get_component(Character)

    previous_age = character_component.age
    character_component.age = age

    if math.floor(previous_age) != math.floor(age):
        db = character.world.get_resource(SimDB).db

        db.execute(
            """UPDATE characters SET age=? WHERE uid=?;""",
            (math.floor(age), character.uid),
        )

        db.commit()


def set_character_birth_date(character: Entity, birth_date: SimDate) -> None:
    """Set the birth date of a character."""

    character.get_component(Character).birth_date = birth_date

    db = character.world.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET birth_date=? WHERE uid=?;""",
        (str(birth_date), character),
    )

    db.commit()


def set_character_death_date(character: Entity, death_date: SimDate) -> None:
    """Set the death date of a character."""

    character.get_component(Character).death_date = death_date

    db = character.world.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET death_date=? WHERE uid=?;""",
        (str(death_date), character),
    )

    db.commit()


def set_relation(
    character_a: Entity, character_b: Entity, relation_type: RelationType
) -> None:
    """Adds a given relation type between two characters."""
    world = character_a.world
    db = world.get_resource(SimDB).db
    cursor = db.cursor()

    # Check that these characters don't already have the given relation.
    result: int = cursor.execute(
        """
        SELECT
            EXISTS(
                SELECT 1
                FROM relations
                WHERE character_id=? AND target_id=? AND relation_type=?
            )
        ;
        """,
        (character_a.uid, character_b.uid, relation_type.name),
    ).fetchone()[0]

    if result == 1:
        return

    cursor.execute(
        """
        INSERT INTO relations (character_id, target_id, relation_type)
        VALUES (?, ?, ?);
        """,
        (character_a.uid, character_b.uid, relation_type.name),
    )

    db.commit()


def unset_relation(
    character_a: Entity, character_b: Entity, relation_type: RelationType
) -> None:
    """Removes a given relation type between two characters."""

    world = character_a.world
    db = world.get_resource(SimDB).db
    cursor = db.cursor()

    cursor.execute(
        """
        DELETE FROM relations
        WHERE character_id=? AND target_id=? AND relation_type=?;
        """,
        (character_a.uid, character_b.uid, relation_type.name),
    )

    db.commit()


def get_relations(character: Entity, relation_type: RelationType) -> list[Entity]:
    """Get all characters related to the given character by the provided relation."""
    world = character.world
    db = world.get_resource(SimDB).db

    cursor = db.cursor()

    result = cursor.execute(
        """
        SELECT target_id
        FROM relations
        WHERE character_id=? AND relation_type=?;
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

    current_date = world.get_resource(SimDate)
    db = world.get_resource(SimDB).db
    cur = db.cursor()

    # Set the spouse references in the component data
    character_a_component.spouse = character_b
    character_b_component.spouse = character_a

    # Update the spouse IDs in the database
    set_relation(character_b, character_a, RelationType.SPOUSE)
    set_relation(character_a, character_b, RelationType.SPOUSE)

    # Create a new marriage entries into the database
    a_to_b = world.entity(
        components=[
            Marriage(character_a, character_b, current_date),
        ]
    )
    character_a_component.marriage = a_to_b
    cur.execute(
        """
        INSERT INTO marriages (uid, character_id, spouse_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (a_to_b.uid, character_a.uid, character_b.uid, current_date.to_iso_str()),
    )

    b_to_a = world.entity(
        components=[
            Marriage(character_b, character_a, current_date),
        ]
    )
    character_b_component.marriage = b_to_a
    cur.execute(
        """
        INSERT INTO marriages (uid, character_id, spouse_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (b_to_a.uid, character_b.uid, character_a.uid, current_date.to_iso_str()),
    )

    db.commit()

    character_a.get_component(CharacterMetrics).data.times_married += 1
    character_b.get_component(CharacterMetrics).data.times_married += 1


def end_marriage(character_a: Entity, character_b: Entity) -> None:
    """Unset the current spouse of a character and end the marriage."""

    world = character_a.world
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

    current_date = world.get_resource(SimDate).to_iso_str()
    db = world.get_resource(SimDB).db
    cur = db.cursor()

    # Update the spouse IDs in the database
    unset_relation(character_b, character_a, RelationType.SPOUSE)
    unset_relation(character_a, character_b, RelationType.SPOUSE)
    unset_relation(character_b, character_a, RelationType.EX_SPOUSE)
    unset_relation(character_a, character_b, RelationType.EX_SPOUSE)

    # Update marriage entries in the database
    assert character_a_component.marriage

    cur.execute(
        """
        UPDATE marriages SET end_date=?
        WHERE uid=?;
        """,
        (current_date, character_a_component.marriage.uid),
    )
    character_a_component.past_marriages.append(character_a_component.marriage)
    character_a_component.marriage = None

    assert character_b_component.marriage

    cur.execute(
        """
        UPDATE marriages SET end_date=?
        WHERE uid=?;
        """,
        (current_date, character_b_component.marriage.uid),
    )
    character_b_component.past_marriages.append(character_b_component.marriage)
    character_b_component.marriage = None

    db.commit()


def start_romantic_affair(character_a: Entity, character_b: Entity) -> None:
    """Start a romantic affair between two characters."""
    world = character_a.world
    character_a_component = character_a.get_component(Character)
    character_b_component = character_b.get_component(Character)

    # Check that both characters are not married
    if character_a_component.lover:
        raise RuntimeError(f"Error: {character_a.name_with_uid} already has a lover.")

    if character_b_component.lover:
        raise RuntimeError(f"Error: {character_b.name_with_uid} already has a lover.")

    current_date = world.get_resource(SimDate)
    db = world.get_resource(SimDB).db
    cur = db.cursor()

    # Set the lover references in the component data
    character_a_component.lover = character_b
    character_b_component.lover = character_a

    # Update the lover IDs in the database
    set_relation(character_b, character_a, RelationType.LOVER)
    set_relation(character_a, character_b, RelationType.LOVER)

    # Create a new romantic affair entries into the database
    a_to_b = world.entity(
        components=[
            RomanticAffair(character_a, character_b, current_date),
        ]
    )
    character_a_component.love_affair = a_to_b
    cur.execute(
        """
        INSERT INTO romantic_affairs (uid, character_id, lover_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (a_to_b.uid, character_b.uid, character_a.uid, current_date.to_iso_str()),
    )

    b_to_a = world.entity(
        components=[
            RomanticAffair(character_b, character_a, current_date),
        ]
    )
    character_b_component.love_affair = b_to_a
    cur.execute(
        """
        INSERT INTO romantic_affairs (uid, character_id, lover_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (b_to_a.uid, character_a.uid, character_b.uid, current_date.to_iso_str()),
    )

    db.commit()


def end_romantic_affair(character_a: Entity, character_b: Entity) -> None:
    """End a romantic affair between two characters."""
    world = character_a.world
    character_a_component = character_a.get_component(Character)
    character_b_component = character_b.get_component(Character)

    # Check that both characters are lovers with each other
    if character_a_component.lover != character_b:
        raise RuntimeError(
            f"Error: {character_a.name_with_uid} is not in a romantic affair with"
            f" {character_b.name_with_uid}."
        )

    if character_b_component.lover != character_a:
        raise RuntimeError(
            f"Error: {character_b.name_with_uid} is not in a romantic affair with"
            f" {character_a.name_with_uid}."
        )

    # Set the spouse references in the component data
    character_a_component.lover = None
    character_b_component.lover = None

    current_date = world.get_resource(SimDate).to_iso_str()
    db = world.get_resource(SimDB).db
    cur = db.cursor()

    # Update the spouse IDs in the database
    unset_relation(character_b, character_a, RelationType.LOVER)
    unset_relation(character_a, character_b, RelationType.LOVER)

    # Update romantic affair entries in the database
    assert character_a_component.love_affair

    cur.execute(
        """
        UPDATE romantic_affairs SET end_date=?
        WHERE uid=?;
        """,
        (current_date, character_a_component.love_affair.uid),
    )
    character_a_component.past_love_affairs.append(character_a_component.love_affair)
    character_a_component.love_affair = None

    assert character_b_component.love_affair

    cur.execute(
        """
        UPDATE romantic_affairs SET end_date=?
        WHERE uid=?;
        """,
        (current_date, character_b_component.love_affair.uid),
    )
    character_b_component.past_love_affairs.append(character_b_component.love_affair)
    character_b_component.love_affair = None

    db.commit()


def set_character_alive(character: Entity, is_alive: bool) -> None:
    """Set is_alive status of a character."""

    character.get_component(Character).is_alive = is_alive

    db = character.world.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET is_alive=? WHERE uid=?;""",
        (is_alive, character.uid),
    )

    db.commit()


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


def init_betrothal(character_a: Entity, character_b: Entity) -> None:
    """Initialize a betrothal between two characters."""
    world = character_a.world
    character_a_component = character_a.get_component(Character)
    character_b_component = character_b.get_component(Character)

    # Check that both characters are not married
    if character_a_component.betrothed_to:
        raise RuntimeError(f"Error: {character_a.name_with_uid} is already betrothed.")

    if character_b_component.betrothed_to:
        raise RuntimeError(f"Error: {character_b.name_with_uid} is already betrothed.")

    current_date = world.get_resource(SimDate)
    db = world.get_resource(SimDB).db
    cur = db.cursor()

    # Update the relations in the database
    set_relation(character_b, character_a, RelationType.BETROTHED)
    set_relation(character_a, character_b, RelationType.BETROTHED)

    # Create a new marriage entries into the database
    a_to_b = world.entity(
        components=[
            Betrothal(character_a, character_b, current_date),
        ]
    )
    character_a_component.betrothed_to = character_b
    character_a_component.betrothal = a_to_b
    cur.execute(
        """
        INSERT INTO betrothals (uid, character_id, betrothed_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (a_to_b.uid, character_b.uid, character_a.uid, current_date.to_iso_str()),
    )

    b_to_a = world.entity(
        components=[
            Betrothal(character_b, character_a, current_date),
        ]
    )
    character_b_component.betrothed_to = character_a
    character_b_component.betrothal = b_to_a
    cur.execute(
        """
        INSERT INTO betrothals (uid, character_id, betrothed_id, start_date)
        VALUES (?, ?, ?, ?);
        """,
        (b_to_a.uid, character_a.uid, character_b.uid, current_date.to_iso_str()),
    )

    db.commit()


def terminate_betrothal(character_a: Entity, character_b: Entity) -> None:
    """Remove the betrothal from the characters."""
    world = character_a.world
    character_a_component = character_a.get_component(Character)
    character_b_component = character_b.get_component(Character)

    if character_a_component.betrothed_to != character_b:
        raise RuntimeError(
            f"Error: {character_a.name_with_uid} is not betrothed to"
            f" {character_b.name_with_uid}."
        )

    if character_b_component.betrothed_to != character_a:
        raise RuntimeError(
            f"Error: {character_b.name_with_uid} is not married to"
            f" {character_a.name_with_uid}."
        )

    current_date = world.get_resource(SimDate).to_iso_str()
    db = world.get_resource(SimDB).db
    cur = db.cursor()

    character_a_current_betrothal = character_a_component.betrothal
    character_b_current_betrothal = character_b_component.betrothal

    assert character_a_current_betrothal is not None
    assert character_b_current_betrothal is not None

    # Update the relations in the database
    unset_relation(character_b, character_a, RelationType.BETROTHED)
    unset_relation(character_a, character_b, RelationType.BETROTHED)

    # Update marriage entries in the database
    cur.execute(
        """
        UPDATE betrothals SET end_date=?
        WHERE uid=?;
        """,
        (current_date, character_a_current_betrothal.uid),
    )
    character_a_component.past_betrothals.append(character_a_current_betrothal)
    character_a_component.betrothal = None
    character_a_component.betrothed_to = None

    cur.execute(
        """
        UPDATE betrothals SET end_date=?
        WHERE uid=?;
        """,
        (current_date, character_b_current_betrothal.uid),
    )
    character_b_component.past_betrothals.append(character_b_current_betrothal)
    character_b_component.betrothal = None
    character_b_component.betrothed_to = None

    db.commit()

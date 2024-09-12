"""Modifier functions for manipulating characters, clans, families, and households."""

from __future__ import annotations

import logging
import math
import random
from typing import Optional

from minerva.characters.components import (
    Character,
    Clan,
    Emperor,
    Family,
    HeadOfClan,
    HeadOfFamily,
    HeadOfHousehold,
    Household,
    LifeStage,
    Sex,
    SexualOrientation,
)
from minerva.characters.succession_helpers import get_succession_depth_chart
from minerva.datetime import SimDate
from minerva.ecs import Active, Event, GameObject
from minerva.life_events.succession import (
    BecameClanHeadEvent,
    BecameEmperorEvent,
    BecameFamilyHeadEvent,
    ClanRemovedFromPlay,
    FamilyRemovedFromPlay,
)
from minerva.relationships.helpers import deactivate_relationships
from minerva.sim_db import SimDB
from minerva.world_map.components import Settlement
from minerva.world_map.helpers import set_settlement_controlling_family

_logger = logging.getLogger(__name__)

# ===================================
# Clan Functions
# ===================================


def set_clan_name(
    clan: GameObject,
    name: str,
) -> None:
    """Set the name of the given clan."""

    clan_component = clan.get_component(Clan)
    clan_component.name = name
    clan.name = name

    db = clan.world.resources.get_resource(SimDB).db
    cur = db.cursor()
    cur.execute(
        """UPDATE clans SET name=? WHERE uid=?;""",
        (name, clan),
    )
    db.commit()


def set_clan_head(
    clan: GameObject,
    character: Optional[GameObject],
) -> None:
    """Set the head of the given clan.

    Parameters
    ----------
    clan
        The clan to modify.
    character
        The new clan head. If None, the current head is removed and not replaced.
    """
    current_date = clan.world.resources.get_resource(SimDate).to_iso_str()
    db = clan.world.resources.get_resource(SimDB).db
    cur = db.cursor()
    clan_component = clan.get_component(Clan)
    former_head: Optional[GameObject] = None

    # Do nothing if already set properly
    if clan_component.head == character:
        return

    # Remove the current household head
    if clan_component.head is not None:
        former_head = clan_component.head
        former_head.remove_component(HeadOfClan)
        clan_component.head = None
        cur.execute(
            """UPDATE clan_heads SET end_date=? where head=?;""",
            (current_date, former_head),
        )

    # Set the new household head
    if character is not None:
        clan_component.head = character
        character.add_component(HeadOfClan(clan=clan))
        cur.execute(
            """INSERT INTO clan_heads (head, clan, start_date) VALUES (?, ?, ?);""",
            (character, clan, current_date),
        )

    cur.execute(
        """UPDATE clans SET head=? WHERE uid=?;""",
        (character, clan),
    )

    db.commit()

    if former_head != character:
        clan.dispatch_event(
            Event(
                event_type="head-change",
                world=clan.world,
                clan=clan,
                former_head=former_head,
                current_head=character,
            )
        )


def set_character_clan(
    character: GameObject,
    clan: Optional[GameObject],
) -> None:
    """Set the current clan of the character.

    Parameters
    ----------
    character
        The character to modify.
    clan
        The clan to add them to. If False, the character is removed from their current
        clan and not added to another.
    """

    character_component = character.get_component(Character)
    former_clan: Optional[GameObject] = None

    # Do nothing if already set properly
    if character_component.clan == clan:
        return

    # Remove them from their current clan
    if character_component.clan is not None:
        former_clan = character_component.clan
        clan_component = former_clan.get_component(Clan)
        clan_component.members.remove(character)
        character_component.clan = None

    # Add the character to their new clan
    if clan is not None:
        clan_component = clan.get_component(Clan)
        clan_component.members.append(character)
        character_component.clan = clan

    db = character.world.resources.get_resource(SimDB).db
    db.execute(
        """UPDATE characters SET clan=? WHERE uid=?;""",
        (clan, character),
    )
    db.commit()

    character.dispatch_event(
        Event(
            event_type="clan-changed",
            world=character.world,
            clan=clan,
            character=character,
            former_clan=former_clan,
        )
    )


def set_character_birth_clan(
    character: GameObject,
    clan: Optional[GameObject],
) -> None:
    """Set the clan that the character was born into."""

    character_component = character.get_component(Character)
    former_clan: Optional[GameObject] = None

    # Do nothing if already set properly
    if character_component.birth_clan == clan:
        return

    # Remove them from their current clan
    if character_component.birth_clan is not None:
        former_clan = character_component.birth_clan
        character_component.birth_clan = None

    # Add the character to their new clan
    if clan is not None:
        character_component.birth_clan = clan

    db = character.world.resources.get_resource(SimDB).db
    db.execute(
        """UPDATE characters SET birth_clan=? WHERE uid=?;""",
        (clan, character),
    )
    db.commit()

    character.dispatch_event(
        Event(
            event_type="birth-clan-changed",
            world=character.world,
            clan=clan,
            character=character,
            former_clan=former_clan,
        )
    )


def set_family_clan(
    family: GameObject,
    clan: Optional[GameObject],
) -> None:
    """Set the current clan for an entire family."""

    family_component = family.get_component(Family)

    if family_component.clan == clan:
        return

    if family_component.clan is not None:
        former_clan = family_component.clan
        clan_component = former_clan.get_component(Clan)
        clan_component.families.remove(family)
        family_component.clan = None

    if clan is not None:
        clan_component = clan.get_component(Clan)
        clan_component.families.append(family)
        family_component.clan = clan

    db = family.world.resources.get_resource(SimDB).db
    db.execute(
        """UPDATE families SET clan=? WHERE uid=?;""",
        (clan, family),
    )
    db.commit()

    for m in family_component.members:
        set_character_clan(m, clan)


# ===================================
# Family Functions
# ===================================


def set_family_name(
    family: GameObject,
    name: str,
) -> None:
    """Set the name of the given family."""
    family_component = family.get_component(Family)

    family.name = name
    family_component.name = name

    db = family.world.resources.get_resource(SimDB).db
    cur = db.cursor()
    cur.execute(
        """UPDATE families SET name=? WHERE uid=?;""",
        (name, family),
    )
    db.commit()


def set_household_family(
    household: GameObject,
    family: Optional[GameObject],
) -> None:
    """Set the family for an entire household."""

    household_component = household.get_component(Household)
    former_family: Optional[GameObject] = None

    if household_component.family == family:
        return

    # Remove from existing family
    if household_component.family is not None:
        former_family = household_component.family
        family_component = former_family.get_component(Family)
        family_component.households.remove(household)
        household_component.family = None

    # Add to new family
    if family is not None:
        family_component = family.get_component(Family)
        family_component.households.append(household)
        household_component.family = family

    # Update family tracking for all characters in the household
    for member in household_component.members:
        set_character_family(member, family)

    db = household.world.resources.get_resource(SimDB).db
    cur = db.cursor()
    cur.execute(
        """UPDATE households SET family=? WHERE uid=?;""",
        (family, household),
    )
    db.commit()


def set_family_head(
    family: GameObject,
    character: Optional[GameObject],
) -> None:
    """Set the current head of a family."""
    current_date = family.world.resources.get_resource(SimDate).to_iso_str()
    db = family.world.resources.get_resource(SimDB).db
    cur = db.cursor()
    family_component = family.get_component(Family)
    former_head: Optional[GameObject] = None

    # Do nothing if already set properly
    if family_component.head == character:
        return

    # Remove the current household head
    if family_component.head is not None:
        former_head = family_component.head
        former_head.remove_component(HeadOfFamily)
        family_component.head = None

        cur.execute(
            """UPDATE family_heads SET end_date=? WHERE head=?;""",
            (current_date, former_head.uid),
        )

    # Set the new household head
    if character is not None:
        character.add_component(HeadOfFamily(family=family))
        family_component.head = character

        cur.execute(
            """INSERT INTO family_heads (head, family, start_date) VALUES (?, ?, ?);""",
            (character, family, current_date),
        )

    cur.execute(
        """UPDATE families SET head=? WHERE uid=?;""",
        (character, family),
    )

    db.commit()

    if former_head != character:
        family.dispatch_event(
            Event(
                event_type="head-change",
                world=family.world,
                family=family,
                former_head=former_head,
                current_head=character,
            )
        )


def set_character_family(
    character: GameObject,
    family: Optional[GameObject],
) -> None:
    """Set a character's current family."""
    character_component = character.get_component(Character)

    former_family: Optional[GameObject] = None

    if character_component.family == family:
        return

    if character_component.family is not None:
        former_family = character_component.family
        family_component = former_family.get_component(Family)
        family_component.members.remove(character)
        character_component.family = None

    if family is not None:
        family_component = family.get_component(Family)
        family_component.members.append(character)
        character_component.family = family

    db = character.world.resources.get_resource(SimDB).db
    cur = db.cursor()
    cur.execute(
        """UPDATE characters SET family=? WHERE uid=?;""",
        (family, character),
    )
    db.commit()

    character.dispatch_event(
        Event(
            event_type="family-change",
            world=character.world,
            former_family=former_family,
            family=family,
            character=character,
        )
    )


def set_family_home_base(family: GameObject, settlement: Optional[GameObject]) -> None:
    """Set the home base for the given family."""
    family_component = family.get_component(Family)

    db = family.world.resources.get_resource(SimDB).db
    cur = db.cursor()

    if family_component.home_base is not None:
        former_home_base = family_component.home_base
        settlement_component = former_home_base.get_component(Settlement)
        settlement_component.families.remove(family)
        family_component.home_base = None
        cur.execute("""UPDATE families SET home_base_id=NULL WHERE uid=?""", (family,))
        if family in settlement_component.political_influence:
            del settlement_component.political_influence[family]

    if settlement is not None:
        settlement_component = settlement.get_component(Settlement)
        settlement_component.families.append(family)
        family_component.home_base = settlement
        cur.execute(
            """UPDATE families SET home_base_id=? WHERE uid=?""",
            (settlement.uid, family),
        )
        if family not in settlement_component.political_influence:
            settlement_component.political_influence[family] = 0

    db.commit()


def remove_clan_from_play(clan: GameObject) -> None:
    """Remove a clan from play."""
    clan_component = clan.get_component(Clan)

    if len(clan_component.active_families) != 0:
        _logger.debug(
            "%s is not empty. Removing families from the clan.",
            clan.name_with_uid,
        )

        for member in [*clan_component.active_families]:
            clan_component.active_families.remove(member)
            clan_component.former_families.add(member)
            set_family_clan(member, None)

    clan.deactivate()
    ClanRemovedFromPlay(clan).dispatch()


def remove_family_from_play(family: GameObject) -> None:
    """Remove a family from play."""
    world = family.world
    family_component = family.get_component(Family)

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

    for _, (settlement, _) in world.get_components((Settlement, Active)):
        if family in settlement.political_influence:
            del settlement.political_influence[family]

        if settlement.controlling_family == family:
            set_settlement_controlling_family(settlement.gameobject, None)

    set_family_clan(family, None)

    family.deactivate()

    FamilyRemovedFromPlay(family).dispatch()


def remove_character_from_play(character: GameObject) -> None:
    """Remove a character from play."""
    world = character.world
    current_date = world.resources.get_resource(SimDate).copy()
    rng = world.resources.get_resource(random.Random)

    character.deactivate()

    heir: Optional[GameObject] = None

    depth_chart = get_succession_depth_chart(character)

    # Get top 3 the eligible heirs
    eligible_heirs = [entry.character_id for entry in depth_chart if entry.is_eligible][
        :3
    ]

    if eligible_heirs:
        # Add selection weights to heirs
        # The second bracket slices the proceeding list to the number of
        # eligible heirs
        heir_weights = [0.8, 0.15, 0.5][: len(eligible_heirs)]

        # Select a random heir from the top 3 with most emphasis on the first
        heir_id = rng.choices(eligible_heirs, heir_weights, k=1)[0]

        heir = world.gameobjects.get_gameobject(heir_id)

    if family_head_component := character.try_component(HeadOfFamily):
        # Perform succession
        family = family_head_component.family
        set_family_head(family, heir)
        if heir is not None:
            BecameFamilyHeadEvent(heir, family).dispatch()

    if clan_head_component := character.try_component(HeadOfClan):
        # Perform succession
        clan = clan_head_component.clan
        set_clan_head(clan, heir)
        if heir is not None:
            BecameClanHeadEvent(heir, clan).dispatch()

    if _ := character.try_component(Emperor):
        # Perform succession
        character.remove_component(Emperor)
        if heir is not None:
            heir.add_component(Emperor())
            BecameEmperorEvent(heir).dispatch()

    character_component = character.get_component(Character)

    if character_component.household is not None:
        former_household = character_component.household
        household_component = former_household.get_component(Household)
        if household_component.head == character:
            set_household_head(former_household, None)

    set_character_household(character, None)

    set_character_death_date(character, current_date)

    if character_component.spouse is not None:
        set_relation_spouse(character_component.spouse, None)
        set_relation_spouse(character, None)

    deactivate_relationships(character)


def set_character_birth_family(
    character: GameObject,
    family: Optional[GameObject],
) -> None:
    """Set the birth family of a character."""
    character_component = character.get_component(Character)

    former_family: Optional[GameObject] = None

    if character_component.birth_family == family:
        return

    if character_component.birth_family is not None:
        former_family = character_component.birth_family
        character_component.birth_family = None

    if family is not None:
        character_component.birth_family = family

    db = character.world.resources.get_resource(SimDB).db
    cur = db.cursor()
    cur.execute(
        """UPDATE characters SET birth_family=? WHERE uid=?;""",
        (family, character),
    )
    db.commit()

    character.dispatch_event(
        Event(
            event_type="birth-family-change",
            world=character.world,
            former_family=former_family,
            family=family,
            character=character,
        )
    )


def merge_family_with(
    source_family: GameObject, destination_family: GameObject
) -> None:
    """Merge a source family into a destination family."""

    # Move all households over to the new family and remove them from the old
    source_family_component = source_family.get_component(Family)
    for household in source_family_component.households:
        set_household_family(household, destination_family)


# ===================================
# Household Functions
# ===================================


def set_household_head(
    household: GameObject,
    character: Optional[GameObject],
) -> None:
    """Set the head of the given household.

    Parameters
    ----------
    household
        The household to modify.
    character
        The new household head. If None, the current head is removed and not replaced.
    """
    db = household.world.resources.get_resource(SimDB).db
    cur = db.cursor()
    household_comp = household.get_component(Household)
    former_head: Optional[GameObject] = None

    # Do nothing if already set properly
    if household_comp.head == character:
        return

    # Remove the current household head
    if household_comp.head is not None:
        former_head = household_comp.head
        former_head.remove_component(HeadOfHousehold)
        household_comp.head = None

    # Set the new household head
    if character is not None:
        household_comp.head = character
        character.add_component(HeadOfHousehold(household=household))

    cur.execute(
        """UPDATE households SET head=? WHERE uid=?;""",
        (character, household),
    )
    db.commit()

    if former_head != character:
        household.dispatch_event(
            Event(
                event_type="head-change",
                world=household.world,
                former_head=former_head,
                current_head=character,
            )
        )


def set_character_household(
    character: GameObject,
    household: Optional[GameObject],
) -> None:
    """Set the household of the given character.

    Parameter
    ---------
    character
        The character to modify.
    household
        The new household to add the character to. If None, the character is
        removed from their current household and not placed in another.
    """

    character_component = character.get_component(Character)
    former_household: Optional[GameObject] = None

    # Do nothing if already set properly
    if character_component.household == household:
        return

    # Remove the character from their current household.
    if character_component.household is not None:
        former_household = character_component.household
        household_component = former_household.get_component(Household)
        household_component.members.remove(character)
        character_component.household = None

    # Add the character to their new household
    if household is not None:
        household_component = household.get_component(Household)
        household_component.members.append(character)
        character_component.household = household

    db = character.world.resources.get_resource(SimDB).db
    cur = db.cursor()
    cur.execute(
        """UPDATE characters SET household=? WHERE uid=?;""",
        (household, character),
    )
    db.commit()

    character.dispatch_event(
        Event(
            "household-change",
            world=character.world,
            character=character,
            former_household=former_household,
            household=household,
        )
    )


def merge_household_with(
    source_household: GameObject, destination_household: GameObject
) -> None:
    """Merge a source household into a destination household.

    This function moves character from the source household to the destination
    household and it updates their current family and clan affiliations to match
    that of the destination household.
    """

    # Move all members over to the new household and remove them from the old
    source_household_component = source_household.get_component(Household)
    destination_household_component = destination_household.get_component(Household)

    for member in source_household_component.members:
        set_character_household(member, destination_household)
        set_character_family(member, destination_household_component.family)

        if destination_household_component.family is not None:
            family_component = destination_household_component.family.get_component(
                Family
            )
            set_character_clan(member, family_component.clan)


# ===================================
# Character Functions
# ===================================


def set_character_first_name(character: GameObject, name: str) -> None:
    """Set a character's first name."""

    character_component = character.get_component(Character)
    character_component.first_name = name
    character.name = character_component.full_name

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET first_name=? WHERE uid=?;""",
        (name, character.uid),
    )

    db.commit()


def set_character_surname(character: GameObject, name: str) -> None:
    """Set the surname of a character."""

    character_component = character.get_component(Character)
    character_component.surname = name
    character.name = character_component.full_name

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET surname=? WHERE uid=?;""",
        (name, character.uid),
    )

    db.commit()


def set_character_birth_surname(character: GameObject, name: str) -> None:
    """Set the birth surname of a character."""

    character.get_component(Character).birth_surname = name

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET birth_surname=? WHERE uid=?;""",
        (name, character.uid),
    )

    db.commit()


def set_character_sex(character: GameObject, sex: Sex) -> None:
    """Set the sex of a character."""

    character.get_component(Character).sex = sex

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET sex=? WHERE uid=?;""",
        (sex, character.uid),
    )

    db.commit()


def set_character_sexual_orientation(
    character: GameObject, orientation: SexualOrientation
) -> None:
    """Set the sexual orientation of a character."""

    character.get_component(Character).sexual_orientation = orientation

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET sexual_orientation=? WHERE uid=?;""",
        (orientation, character.uid),
    )

    db.commit()


def set_character_life_stage(character: GameObject, life_stage: LifeStage) -> None:
    """Set the life stage of a character."""

    character.get_component(Character).life_stage = life_stage

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET life_stage=? WHERE uid=?;""",
        (life_stage, character.uid),
    )

    db.commit()


def set_character_age(character: GameObject, age: float) -> None:
    """Set the age of a character."""
    character_component = character.get_component(Character)

    previous_age = character_component.age
    character_component.age = age

    if math.floor(previous_age) != math.floor(age):
        db = character.world.resources.get_resource(SimDB).db

        db.execute(
            """UPDATE characters SET age=? WHERE uid=?;""",
            (math.floor(age), character.uid),
        )

        db.commit()


def set_character_birth_date(character: GameObject, birth_date: SimDate) -> None:
    """Set the birth date of a character."""

    character.get_component(Character).birth_date = birth_date

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET birth_date=? WHERE uid=?;""",
        (str(birth_date), character),
    )

    db.commit()


def set_character_death_date(character: GameObject, death_date: SimDate) -> None:
    """Set the death date of a character."""

    character.get_component(Character).death_date = death_date

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET death_date=? WHERE uid=?;""",
        (str(death_date), character),
    )

    db.commit()


def set_character_mother(character: GameObject, mother: Optional[GameObject]) -> None:
    """Set the mother of a character."""

    character_component = character.get_component(Character)

    if character_component.mother is not None:
        character_component.mother = None

    if mother is not None:
        character_component.mother = mother

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET mother=? WHERE uid=?;""",
        (mother, character),
    )

    db.commit()


def set_character_heir(character: GameObject, heir: Optional[GameObject]) -> None:
    """Set the heir of a character."""

    character_component = character.get_component(Character)
    former_heir: Optional[GameObject] = None

    if character_component.heir is not None:
        former_heir = character_component.heir
        character_component.heir = None

    if heir is not None:
        character_component.heir = heir

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET heir=? WHERE uid=?;""",
        (heir, character),
    )

    db.commit()

    character.dispatch_event(
        Event(
            event_type="heir-change",
            world=character.world,
            character=character,
            former_heir=former_heir,
            heir=heir,
        )
    )


def set_character_father(character: GameObject, father: Optional[GameObject]) -> None:
    """Set the father of a character."""

    character.get_component(Character).father = father

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET father=? WHERE uid=?;""",
        (father, character.uid),
    )

    db.commit()


def set_character_biological_father(
    character: GameObject, father: Optional[GameObject]
) -> None:
    """Set the biological father of a character."""

    character.get_component(Character).biological_father = father

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET biological_father=? WHERE uid=?;""",
        (father, character.uid),
    )

    db.commit()


def set_relation_spouse(character: GameObject, spouse: Optional[GameObject]) -> None:
    """Set the spouse of a character."""

    character_component = character.get_component(Character)
    current_date = character.world.resources.get_resource(SimDate).to_iso_str()
    db = character.world.resources.get_resource(SimDB).db
    cur = db.cursor()

    if character_component.spouse is not None:
        previous_spouse = character_component.spouse
        character_component.spouse = None

        cur.execute(
            """UPDATE characters SET spouse=? WHERE uid=?;""",
            (None, character.uid),
        )

        cur.execute(
            """UPDATE marriages SET end_date=? WHERE spouse_id=? and character_id=?;""",
            (current_date, previous_spouse.uid, character.uid),
        )

    if spouse is not None:
        character_component.spouse = spouse

        cur.execute(
            """
            INSERT INTO marriages (character_id, spouse_id, start_date)
            VALUES (?, ?, ?);
            """,
            (character.uid, spouse.uid, current_date),
        )

        cur.execute(
            """UPDATE characters SET spouse=? WHERE uid=?;""",
            (spouse.uid, character.uid),
        )

    db.commit()


def set_relation_partner(character: GameObject, partner: Optional[GameObject]) -> None:
    """Set the partner of a character."""

    character.get_component(Character).partner = partner

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET partner=? WHERE uid=?;""",
        (partner, character.uid),
    )

    db.commit()


def set_relation_lover(character: GameObject, lover: Optional[GameObject]) -> None:
    """Set the lover of a character."""

    character.get_component(Character).lover = lover

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET lover=? WHERE uid=?;""",
        (lover, character.uid),
    )

    db.commit()


def set_character_alive(character: GameObject, is_alive: bool) -> None:
    """Set is_alive status of a character."""

    character.get_component(Character).is_alive = is_alive

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """UPDATE characters SET is_alive=? WHERE uid=?;""",
        (is_alive, character.uid),
    )

    db.commit()


def set_relation_sibling(character: GameObject, sibling: GameObject) -> None:
    """Set a character as being a sibling to the first.

    Parameters
    ----------
    character
        The character to modify.
    sibling
        The character to set as the sibling.
    """

    character.get_component(Character).siblings.append(sibling)

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """
        INSERT INTO siblings (character_id, sibling_id) VALUES (?, ?);
        """,
        (character.uid, sibling.uid),
    )

    db.commit()


def set_relation_child(character: GameObject, child: GameObject) -> None:
    """Set a character as being a child to the first."""

    character.get_component(Character).children.append(child)

    db = character.world.resources.get_resource(SimDB).db

    db.execute(
        """
        INSERT INTO children (character_id, child_id) VALUES (?, ?);
        """,
        (character.uid, child.uid),
    )

    db.commit()

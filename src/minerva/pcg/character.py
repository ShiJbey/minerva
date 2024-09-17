"""Character Generation Classes and Functions."""

from __future__ import annotations

import pathlib
import random
from typing import Optional, Union

from ordered_set import OrderedSet

from minerva.characters.betrothal_data import BetrothalTracker
from minerva.characters.components import (
    Boldness,
    Character,
    Clan,
    Compassion,
    Diplomacy,
    DreadMotive,
    Family,
    FamilyMotive,
    Fertility,
    Greed,
    HappinessMotive,
    Honor,
    HonorMotive,
    Household,
    Intrigue,
    Learning,
    Lifespan,
    LifeStage,
    Luck,
    MarriageTracker,
    Martial,
    MoneyMotive,
    PowerMotive,
    Prowess,
    Rationality,
    RespectMotive,
    RomancePropensity,
    RomanticAffairTracker,
    Sex,
    SexMotive,
    SexualOrientation,
    Sociability,
    SpeciesLibrary,
    SpeciesType,
    Stewardship,
    Vengefulness,
    ViolencePropensity,
    WantForChildren,
    WantForMarriage,
    WantForPower,
    WantToWork,
    Zeal,
)
from minerva.characters.helpers import (
    set_character_biological_father,
    set_character_birth_clan,
    set_character_birth_family,
    set_character_birth_surname,
    set_character_clan,
    set_character_family,
    set_character_father,
    set_character_household,
    set_character_mother,
    set_character_surname,
    set_clan_head,
    set_clan_name,
    set_family_clan,
    set_family_head,
    set_family_home_base,
    set_household_family,
    set_household_head,
    set_relation_child,
    set_relation_sibling,
    start_marriage,
)
from minerva.characters.succession_helpers import set_current_ruler
from minerva.config import Config
from minerva.constants import CLAN_COLORS_PRIMARY, CLAN_COLORS_SECONDARY
from minerva.ecs import Active, Event, GameObject, World
from minerva.life_events.base_types import LifeEventHistory
from minerva.relationships.base_types import RelationshipManager
from minerva.sim_db import SimDB
from minerva.stats.base_types import StatManager, StatusEffectManager
from minerva.stats.helpers import default_stat_calc_strategy
from minerva.traits.base_types import TraitManager
from minerva.world_map.components import Settlement
from minerva.world_map.helpers import set_settlement_controlling_family


class CharacterNameFactory:
    """Generates names for characters."""

    __slots__ = (
        "_first_name_groups",
        "_surnames",
        "_rng",
    )

    _first_name_groups: dict[Sex, list[str]]
    _surnames: list[str]
    _rng: random.Random

    def __init__(self, seed: Optional[Union[int, str]] = None) -> None:
        self._first_name_groups = {Sex.MALE: [], Sex.FEMALE: []}
        self._surnames = []
        self._rng = random.Random(seed)

    def set_seed(self, seed: Union[int, str]) -> None:
        """Set the seed for the random number generator."""

        self._rng.seed(seed)

    def generate_first_name(self, sex: Sex) -> str:
        """Generate a first name."""

        if len(self._first_name_groups[sex]) == 0:
            raise ValueError(f"No first names found for sex ({sex.name})")

        return self._rng.choice(self._first_name_groups[sex])

    def generate_surname(
        self,
    ) -> str:
        """Generate a surname."""

        if len(self._surnames) == 0:
            raise ValueError("No surnames found.")

        return self._rng.choice(self._surnames)

    def register_first_names(self, sex: Sex, names: list[str]) -> None:
        """Add a collection of first names."""

        for n in names:
            self._first_name_groups[sex].append(n)

    def register_surnames(self, names: list[str]) -> None:
        """Add a collection of surnames."""

        for n in names:
            self._surnames.append(n)

    def load_first_names(
        self,
        sex: Sex,
        filepath: Union[str, pathlib.Path],
    ) -> None:
        """Load first names from a text file."""

        with open(filepath, "r", encoding="utf8") as f:
            names = f.readlines()  # Each line is a different name
            names = [n.strip() for n in names]  # Strip newlines
            names = [n for n in names if n]  # Filter empty lines

        self.register_first_names(sex, names)

    def load_surnames(
        self,
        filepath: Union[str, pathlib.Path],
    ) -> None:
        """Load surnames from a text file."""

        with open(filepath, "r", encoding="utf8") as f:
            names = f.readlines()  # Each line is a different name
            names = [n.strip() for n in names]  # Strip newlines
            names = [n for n in names if n]  # Filter empty lines

        self.register_surnames(names)

    def clear(self):
        """Clear all name data."""

        self._first_name_groups = {Sex.MALE: [], Sex.FEMALE: []}
        self._surnames = []


def generate_random_character_age(
    world: World,
    species: SpeciesType,
    life_stage: LifeStage,
) -> float:
    """Set's the character to the given life stage and generates a valid age."""

    rng = world.resources.get_resource(random.Random)

    if life_stage == LifeStage.SENIOR:
        return rng.randint(species.senior_age, species.lifespan[1])
    elif life_stage == LifeStage.ADULT:
        return rng.randint(species.adult_age, species.senior_age - 1)
    elif life_stage == LifeStage.YOUNG_ADULT:
        return rng.randint(species.young_adult_age, species.adult_age - 1)
    elif life_stage == LifeStage.ADOLESCENT:
        return rng.randint(species.adolescent_age, species.young_adult_age - 1)

    return rng.randint(0, species.adolescent_age - 1)


def generate_character(
    world: World,
    *,
    first_name: str = "",
    surname: str = "",
    species: str = "",
    sex: Optional[Sex] = None,
    sexual_orientation: Optional[SexualOrientation] = None,
    life_stage: Optional[LifeStage] = None,
    age: Optional[int] = None,
) -> GameObject:
    """Create a new character."""
    name_factory = world.resources.get_resource(CharacterNameFactory)
    rng = world.resources.get_resource(random.Random)

    if life_stage is not None and age is not None:
        raise ValueError(
            "Cannot specify life stage and age when generating a character."
        )

    # Step 0: Generate a species
    species_library = world.resources.get_resource(SpeciesLibrary)

    if species:
        chosen_species = species_library.get_species(species)
    else:
        species_choices, weights = tuple(
            zip(
                *[
                    (entry, entry.spawn_frequency)
                    for entry in species_library.species.values()
                    if entry.spawn_frequency > 0
                ]
            )
        )

        if len(species_choices) == 0:
            raise RuntimeError("No eligible species found for character generation.")

        chosen_species: SpeciesType = rng.choices(
            population=species_choices, weights=weights
        )[0]

    # Step 1: Generate a sex
    chosen_sex = sex if sex is not None else rng.choice(list(Sex))

    # Step 2: Generate a sexual orientation
    chosen_sexual_orientation = (
        sexual_orientation
        if sexual_orientation is not None
        else rng.choice(list(SexualOrientation))
    )

    # Step 3: Generate first name
    chosen_first_name = (
        first_name if first_name else name_factory.generate_first_name(chosen_sex)
    )

    # Step 4: Generate surname
    chosen_surname = surname if surname else name_factory.generate_surname()

    # Step 5a: Generate an age and a life stage
    chosen_life_stage = rng.choice(list(LifeStage))
    chosen_age = generate_random_character_age(
        world,
        chosen_species,
        chosen_life_stage,
    )

    # Step 5b: Generate an age if given a life stage
    if life_stage is not None:
        chosen_life_stage = life_stage
        chosen_age = generate_random_character_age(
            world,
            chosen_species,
            chosen_life_stage,
        )

    # Step 5c: Generate a life state of given an age
    if age is not None:
        chosen_age = age
        chosen_life_stage = chosen_species.get_life_stage_for_age(chosen_age)

    obj = world.gameobjects.spawn_gameobject()
    obj.metadata["object_type"] = "character"
    character = obj.add_component(
        Character(
            first_name=chosen_first_name,
            surname=chosen_surname,
            birth_surname=chosen_surname,
            sex=chosen_sex,
            sexual_orientation=chosen_sexual_orientation,
            life_stage=chosen_life_stage,
            age=chosen_age,
            species=chosen_species,
        )
    )

    obj.add_component(TraitManager())
    obj.add_component(StatusEffectManager())
    obj.add_component(RelationshipManager())
    obj.add_component(LifeEventHistory())
    obj.add_component(StatManager())
    obj.add_component(MarriageTracker())
    obj.add_component(RomanticAffairTracker())
    obj.add_component(BetrothalTracker())

    # Create all the stat components and add them to the stats class for str look-ups
    obj.add_component(
        Lifespan(
            default_stat_calc_strategy,
            rng.randint(chosen_species.lifespan[0], chosen_species.lifespan[1]),
        )
    )
    obj.add_component(Fertility(default_stat_calc_strategy))
    obj.add_component(Diplomacy(default_stat_calc_strategy))
    obj.add_component(Martial(default_stat_calc_strategy))
    obj.add_component(Stewardship(default_stat_calc_strategy))
    obj.add_component(Intrigue(default_stat_calc_strategy))
    obj.add_component(Learning(default_stat_calc_strategy))
    obj.add_component(Prowess(default_stat_calc_strategy))
    obj.add_component(Boldness(default_stat_calc_strategy))
    obj.add_component(Compassion(default_stat_calc_strategy))
    obj.add_component(Greed(default_stat_calc_strategy))
    obj.add_component(Honor(default_stat_calc_strategy))
    obj.add_component(Rationality(default_stat_calc_strategy))
    obj.add_component(Sociability(default_stat_calc_strategy))
    obj.add_component(Vengefulness(default_stat_calc_strategy))
    obj.add_component(Zeal(default_stat_calc_strategy))
    obj.add_component(Luck(default_stat_calc_strategy))
    obj.add_component(RomancePropensity(default_stat_calc_strategy))
    obj.add_component(ViolencePropensity(default_stat_calc_strategy))
    obj.add_component(WantForPower(default_stat_calc_strategy))
    obj.add_component(WantForChildren(default_stat_calc_strategy))
    obj.add_component(WantToWork(default_stat_calc_strategy))
    obj.add_component(WantForMarriage(default_stat_calc_strategy))
    obj.add_component(MoneyMotive(default_stat_calc_strategy))
    obj.add_component(PowerMotive(default_stat_calc_strategy))
    obj.add_component(RespectMotive(default_stat_calc_strategy))
    obj.add_component(HappinessMotive(default_stat_calc_strategy))
    obj.add_component(FamilyMotive(default_stat_calc_strategy))
    obj.add_component(HonorMotive(default_stat_calc_strategy))
    obj.add_component(SexMotive(default_stat_calc_strategy))
    obj.add_component(DreadMotive(default_stat_calc_strategy))

    db = world.resources.get_resource(SimDB).db

    db.execute(
        """
        INSERT INTO characters
        (uid, first_name, surname, birth_surname, sex, sexual_orientation, life_stage, is_alive, age)
        VALUES
        (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """,
        (
            obj.uid,
            character.first_name,
            character.surname,
            character.birth_surname,
            character.sex,
            character.sexual_orientation,
            character.life_stage,
            character.is_alive,
            character.age,
        ),
    )

    db.commit()

    return obj


def generate_spouse_for(character: GameObject) -> GameObject:
    """Generate a spouse for the given character."""

    spouse_sex: Optional[Sex] = None

    character_component = character.get_component(Character)

    if character_component.sexual_orientation == SexualOrientation.HETEROSEXUAL:
        if character_component.sex == Sex.MALE:
            spouse_sex = Sex.FEMALE
        else:
            spouse_sex = Sex.MALE

    elif character_component.sexual_orientation == SexualOrientation.HOMOSEXUAL:
        if character_component.sex == Sex.MALE:
            spouse_sex = Sex.MALE
        else:
            spouse_sex = Sex.FEMALE

    return generate_character(
        world=character.world,
        sex=spouse_sex,
    )


def generate_child_from(mother: GameObject, father: GameObject) -> GameObject:
    """Generate a child from the given parents."""

    return generate_character(world=mother.world, life_stage=LifeStage.CHILD)


def generate_household(world: World) -> GameObject:
    """Create a new household."""

    household = world.gameobjects.spawn_gameobject()
    household.add_component(Household())
    household.name = "Household"

    db = world.resources.get_resource(SimDB).db

    db.execute(
        """
        INSERT INTO households
        (uid)
        VALUES (?);
        """,
        (household.uid,),
    )

    db.commit()

    world.events.dispatch_event(
        Event(event_type="household-added", world=world, household=household)
    )

    return household


def generate_family(world: World, name: str = "") -> GameObject:
    """Create a new family."""

    character_name_factory = world.resources.get_resource(CharacterNameFactory)
    db = world.resources.get_resource(SimDB).db

    family = world.gameobjects.spawn_gameobject()
    family.metadata["object_type"] = "family"
    family_name = name if name else character_name_factory.generate_surname()
    family.add_component(Family(name=family_name))
    family.name = f"{family_name}"

    db.execute(
        """
        INSERT INTO families
        (uid, name)
        VALUES (?, ?);
        """,
        (family.uid, family.name),
    )

    db.commit()

    world.events.dispatch_event(
        Event(
            event_type="family-added",
            world=world,
            family=family,
        )
    )

    return family


def generate_clan(world: World, name: str = "") -> GameObject:
    """Create a new clan."""
    rng = world.resources.get_resource(random.Random)
    character_name_factory = world.resources.get_resource(ClanNameFactory)
    db = world.resources.get_resource(SimDB).db

    clan = world.gameobjects.spawn_gameobject()
    clan.metadata["object_type"] = "clan"
    clan_name = name if name else character_name_factory.generate_name()
    clan_component = clan.add_component(Clan(name=clan_name))
    clan_component.color_primary = rng.choice(CLAN_COLORS_PRIMARY)
    clan_component.color_secondary = rng.choice(CLAN_COLORS_SECONDARY)
    clan.name = f"{clan_name}"

    db.execute(
        """
        INSERT INTO clans
        (uid, name)
        VALUES (?, ?);
        """,
        (clan.uid, clan_name),
    )

    db.commit()

    world.events.dispatch_event(
        Event(
            event_type="clan-added",
            world=world,
            clan=clan,
        )
    )

    return clan


class ClanNameFactory:
    """Generates names for clans."""

    __slots__ = ("_names", "_rng")

    _names: list[str]
    _rng: random.Random

    def __init__(self, seed: Optional[Union[str, int]] = None) -> None:
        self._names = []
        self._rng = random.Random(seed)

    def generate_name(self) -> str:
        """Generate a new clan name."""

        if len(self._names) == 0:
            raise ValueError("No clan names were found.")

        return self._rng.choice(self._names)

    def register_names(self, names: list[str]) -> None:
        """Add potential names to the factory."""

        for n in names:
            self._names.append(n)

    def load_names(self, filepath: Union[str, pathlib.Path]) -> None:
        """Load potential names from a text file."""

        with open(filepath, "r", encoding="utf8") as f:
            names = f.readlines()  # Each line is a different name
            names = [n.strip() for n in names]  # Strip newlines
            names = [n for n in names if n]  # Filter empty lines

        self.register_names(names)

    def clear(self) -> None:
        """Clear all potential names."""

        self._names = []


def generate_initial_clans(world: World) -> None:
    """Generates initial clans and families."""

    # config = world.resources.get_resource(Config)
    rng = world.resources.get_resource(random.Random)

    # Generate the initial clans
    _generate_clans(world)

    families = [
        world.gameobjects.get_gameobject(uid)
        for uid, _ in world.get_components((Family, Active))
    ]

    # Assign families to settlements
    settlements = [
        world.gameobjects.get_gameobject(uid)
        for uid, _ in world.get_components((Settlement, Active))
    ]

    unassigned_clans = [*families]
    rng.shuffle(unassigned_clans)

    unassigned_settlements = [*settlements]

    # Designate a family as the royal family
    clan_heads = [
        clan.head
        for _, (clan, _) in world.get_components((Clan, Active))
        if clan.head is not None
    ]

    # Start the first dynasty
    chosen_emperor = rng.choice(clan_heads)
    set_current_ruler(world, chosen_emperor)

    emperor_family = chosen_emperor.get_component(Character).family
    assert emperor_family is not None, "Emperor family cannot be none"

    for family in OrderedSet([emperor_family, *families]):
        if unassigned_settlements:
            home_base = unassigned_settlements.pop()
            set_settlement_controlling_family(home_base, family)
            set_family_home_base(family, home_base)
            continue

        set_family_home_base(family, rng.choice(settlements))


def _generate_clans(world: World) -> list[GameObject]:
    """Generate initial clans."""
    rng = world.resources.get_resource(random.Random)
    config = world.resources.get_resource(Config)

    clans: list[GameObject] = []

    for _ in range(config.n_initial_clans):
        # Create an empty clan
        clan = generate_clan(world)
        clans.append(clan)

        # Track the family heads that are generated. The head of the first family
        # will become the head of the clan. They will be the first in the list.
        family_heads: list[GameObject] = []

        n_families_to_generate = rng.randint(1, config.max_families_per_clan)

        for _ in range(n_families_to_generate):
            # Create a new family and add it to the clan
            family = generate_family(world)
            family_surname = family.get_component(Family).name
            set_family_clan(family, clan)

            # Track the household heads that are generated. The head of the first
            # household will become the family head.
            household_heads: list[GameObject] = []

            n_household_to_generate: int = rng.randint(
                1, config.max_households_per_family
            )

            for _ in range(n_household_to_generate):
                # Create a new household head
                household_head = generate_character(
                    world,
                    life_stage=LifeStage.ADULT,
                    sex=Sex.MALE,
                    sexual_orientation=SexualOrientation.HETEROSEXUAL,
                )

                set_character_surname(household_head, family_surname)
                set_character_birth_surname(household_head, family_surname)

                household_heads.append(household_head)

                set_character_clan(household_head, clan)
                set_character_family(household_head, family)

                # Generate a new household and add it to the family
                household = generate_household(world)
                set_household_family(household, family)
                set_household_head(household, household_head)
                set_character_household(household_head, household)

                # Generate a spouse for the household head
                spouse = generate_spouse_for(household_head)

                set_character_surname(spouse, family_surname)
                set_character_clan(spouse, clan)
                set_character_family(spouse, family)
                set_character_household(spouse, household)

                # Update the relationship between the household head and spouse
                start_marriage(household_head, spouse)

                n_children = rng.randint(0, config.max_children_per_household)

                generated_children: list[GameObject] = []

                for _ in range(n_children):
                    child = generate_child_from(spouse, household_head)

                    set_character_surname(child, family_surname)

                    set_character_clan(child, clan)
                    set_character_family(child, family)
                    set_character_household(child, household)
                    set_character_birth_family(child, family)

                    set_relation_child(household_head, child)
                    set_relation_child(spouse, child)
                    set_character_father(child, household_head)
                    set_character_mother(child, spouse)
                    set_character_biological_father(child, household_head)
                    set_character_birth_clan(child, clan)

                    generated_children.append(child)

                for i, c1 in enumerate(generated_children):
                    if i + 1 >= len(generated_children):
                        continue

                    c2 = generated_children[i + 1]

                    if c1 != c2:
                        set_relation_sibling(c1, c2)
                        set_relation_sibling(c2, c1)

            # Set the family head
            set_family_head(family, household_heads[0])
            family_heads.append(household_heads[0])

        # Set the clan head
        set_clan_head(clan, family_heads[0])
        set_clan_name(clan, family_heads[0].get_component(Character).surname)
        set_clan_name(clan, family_heads[0].get_component(Character).surname)

    return clans

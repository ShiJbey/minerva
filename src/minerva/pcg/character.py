"""Character Generation Classes and Functions."""

from __future__ import annotations

import pathlib
import random
from typing import Optional, Union

from minerva.characters.components import (
    Boldness,
    Character,
    Clan,
    Compassion,
    Diplomacy,
    Family,
    Fertility,
    Greed,
    Honor,
    Household,
    Intrigue,
    Learning,
    Lifespan,
    LifeStage,
    Luck,
    Martial,
    Prowess,
    Rationality,
    RomancePropensity,
    Sex,
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
from minerva.ecs import Event, GameObject, World
from minerva.life_events.base_types import EventHistory
from minerva.relationships.base_types import RelationshipManager
from minerva.sim_db import SimDB
from minerva.stats.base_types import StatManager, StatusEffectManager
from minerva.traits.base_types import TraitManager


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
    obj.add_component(EventHistory())
    stats = obj.add_component(StatManager())

    # Create all the stat components and add them to the stats class for str look-ups
    stats.stats["Lifespan"] = obj.add_component(Lifespan())
    stats.stats["Fertility"] = obj.add_component(Fertility())
    stats.stats["Diplomacy"] = obj.add_component(Diplomacy())
    stats.stats["Martial"] = obj.add_component(Martial())
    stats.stats["Stewardship"] = obj.add_component(Stewardship())
    stats.stats["Intrigue"] = obj.add_component(Intrigue())
    stats.stats["Learning"] = obj.add_component(Learning())
    stats.stats["Prowess"] = obj.add_component(Prowess())
    stats.stats["Boldness"] = obj.add_component(Boldness())
    stats.stats["Compassion"] = obj.add_component(Compassion())
    stats.stats["Greed"] = obj.add_component(Greed())
    stats.stats["Honor"] = obj.add_component(Honor())
    stats.stats["Rationality"] = obj.add_component(Rationality())
    stats.stats["Sociability"] = obj.add_component(Sociability())
    stats.stats["Vengefulness"] = obj.add_component(Vengefulness())
    stats.stats["Zeal"] = obj.add_component(Zeal())
    stats.stats["Luck"] = obj.add_component(Luck())
    stats.stats["RomancePropensity"] = obj.add_component(RomancePropensity())
    stats.stats["ViolencePropensity"] = obj.add_component(ViolencePropensity())
    stats.stats["WantForPower"] = obj.add_component(WantForPower())
    stats.stats["WantForChildren"] = obj.add_component(WantForChildren())
    stats.stats["WantToWork"] = obj.add_component(WantToWork())
    stats.stats["WantForMarriage"] = obj.add_component(WantForMarriage())

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


def generate_family(world: World) -> GameObject:
    """Create a new family."""

    character_name_factory = world.resources.get_resource(CharacterNameFactory)
    db = world.resources.get_resource(SimDB).db

    family = world.gameobjects.spawn_gameobject()
    family_name = character_name_factory.generate_surname()
    family.add_component(Family(name=family_name))
    family.name = family_name

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


def generate_clan(world: World) -> GameObject:
    """Create a new clan."""

    character_name_factory = world.resources.get_resource(ClanNameFactory)
    db = world.resources.get_resource(SimDB).db

    clan = world.gameobjects.spawn_gameobject()
    clan_name = character_name_factory.generate_name()
    clan.add_component(Clan(name=clan_name))
    clan.name = clan_name

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

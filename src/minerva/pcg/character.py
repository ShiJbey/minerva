"""Character Generation Classes and Functions."""

from __future__ import annotations

import random
from typing import Optional

from minerva.actions.base_types import AIBrain, AIContext, SchemeManager
from minerva.actions.selection_strategies import MaxUtilActionSelectStrategy
from minerva.actions.sensors import (
    TerritoriesControlledByOpps,
    TerritoriesInRevoltSensor,
    UnControlledTerritoriesSensor,
    UnexpandedTerritoriesSensor,
)
from minerva.characters.components import (
    Boldness,
    Character,
    Compassion,
    Diplomacy,
    Family,
    FamilyPrestige,
    Fertility,
    Greed,
    Honor,
    Intelligence,
    Intrigue,
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
    Species,
    SpeciesLibrary,
    Stewardship,
    Vengefulness,
)
from minerva.characters.helpers import (
    set_character_biological_father,
    set_character_birth_date,
    set_character_birth_family,
    set_character_birth_surname,
    set_character_family,
    set_character_father,
    set_character_mother,
    set_character_surname,
    set_family_head,
    set_relation_child,
    set_relation_sibling,
    start_marriage,
)
from minerva.characters.metric_data import CharacterMetrics
from minerva.characters.war_data import WarTracker
from minerva.config import Config
from minerva.datetime import SimDate
from minerva.ecs import Entity, World
from minerva.life_events.base_types import LifeEventHistory
from minerva.pcg.base_types import (
    BabyFactory,
    CharacterFactory,
    CharacterGenOptions,
    FamilyFactory,
    FamilyGenOptions,
    NameFactory,
    PCGFactories,
)
from minerva.relationships.base_types import RelationshipManager
from minerva.sim_db import SimDB
from minerva.simulation_events import SimulationEvents
from minerva.stats.base_types import StatusEffectManager
from minerva.stats.helpers import default_stat_calc_strategy
from minerva.traits.base_types import Trait, TraitLibrary, TraitManager
from minerva.traits.helpers import (
    add_trait,
    get_personality_traits,
    has_conflicting_trait,
    has_trait,
)


class DefaultCharacterFactory(CharacterFactory):
    """Built-in implementation of a character factory."""

    __slots__ = (
        "male_first_name_factory",
        "female_first_name_factory",
        "surname_factory",
    )

    male_first_name_factory: NameFactory
    female_first_name_factory: NameFactory
    surname_factory: NameFactory

    def __init__(
        self,
        male_first_name_factory: NameFactory,
        female_first_name_factory: NameFactory,
        surname_factory: NameFactory,
    ) -> None:
        super().__init__()
        self.male_first_name_factory = male_first_name_factory
        self.female_first_name_factory = female_first_name_factory
        self.surname_factory = surname_factory

    @staticmethod
    def generate_random_character_age(
        world: World,
        species: Species,
        life_stage: LifeStage,
    ) -> float:
        """Set's the character to the given life stage and generates a valid age."""

        rng = world.get_resource(random.Random)

        if life_stage == LifeStage.SENIOR:
            return rng.randint(species.senior_age, species.lifespan[1])
        elif life_stage == LifeStage.ADULT:
            return rng.randint(species.adult_age, species.senior_age - 1)
        elif life_stage == LifeStage.YOUNG_ADULT:
            return rng.randint(species.young_adult_age, species.adult_age - 1)
        elif life_stage == LifeStage.ADOLESCENT:
            return rng.randint(species.adolescent_age, species.young_adult_age - 1)

        return rng.randint(0, species.adolescent_age - 1)

    def generate_character(self, world: World, options: CharacterGenOptions) -> Entity:
        """Create a new character."""
        rng = world.get_resource(random.Random)

        obj = world.entity()

        if options.life_stage is not None and options.age is not None:
            raise ValueError(
                "Cannot specify life stage and age when generating a character."
            )

        # Step 0: Generate a species
        species_library = world.get_resource(SpeciesLibrary)

        if options.species:
            chosen_species = species_library.get_species(options.species)
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
                raise RuntimeError(
                    "No eligible species found for character generation."
                )

            chosen_species: Species = rng.choices(
                population=species_choices, weights=weights
            )[0]

        # Step 1: Generate a sex
        chosen_sex = options.sex if options.sex is not None else rng.choice(list(Sex))

        # Step 2: Generate a sexual orientation
        chosen_sexual_orientation = (
            options.sexual_orientation
            if options.sexual_orientation is not None
            else rng.choice(list(SexualOrientation))
        )

        # Step 3: Generate first name
        if options.first_name:
            chosen_first_name = options.first_name
        elif chosen_sex == Sex.MALE:
            chosen_first_name = self.male_first_name_factory.generate_name(obj)
        else:
            chosen_first_name = self.female_first_name_factory.generate_name(obj)

        # Step 4: Generate surname
        chosen_surname = (
            options.surname
            if options.surname
            else self.surname_factory.generate_name(obj)
        )

        # Step 5a: Generate an age and a life stage
        chosen_life_stage = rng.choice(list(LifeStage))
        chosen_age = self.generate_random_character_age(
            world,
            chosen_species,
            chosen_life_stage,
        )

        # Step 5b: Generate an age if given a life stage
        if options.life_stage is not None:
            chosen_life_stage = options.life_stage
            chosen_age = self.generate_random_character_age(
                world,
                chosen_species,
                chosen_life_stage,
            )

        # Step 5c: Generate a life state of given an age
        if options.age is not None:
            chosen_age = options.age
            chosen_life_stage = chosen_species.get_life_stage_for_age(chosen_age)

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
        obj.name = character.full_name

        obj.add_component(TraitManager())
        obj.add_component(StatusEffectManager())
        obj.add_component(CharacterMetrics())
        obj.add_component(RelationshipManager())
        obj.add_component(LifeEventHistory())
        obj.add_component(
            AIBrain(
                context=AIContext(
                    world,
                    character=obj,
                    sensors=[
                        TerritoriesInRevoltSensor(),
                        UnexpandedTerritoriesSensor(),
                        UnControlledTerritoriesSensor(),
                        TerritoriesControlledByOpps(),
                    ],
                ),
                action_selection_strategy=MaxUtilActionSelectStrategy(),
                # action_selection_strategy=WeightedActionSelectStrategy(rng=rng),
            )
        )
        obj.add_component(SchemeManager())

        # Create all the stat components and add them to the stats class for str look-ups
        obj.add_component(
            Lifespan(
                default_stat_calc_strategy,
                rng.randint(chosen_species.lifespan[0], chosen_species.lifespan[1]),
            )
        )
        obj.add_component(
            Fertility(
                default_stat_calc_strategy,
                base_value=(
                    rng.randint(
                        0,
                        chosen_species.get_max_fertility(chosen_sex, chosen_life_stage),
                    )
                    if options.randomize_stats
                    else chosen_species.get_max_fertility(chosen_sex, chosen_life_stage)
                ),
            )
        )
        obj.add_component(
            Diplomacy(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Martial(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Stewardship(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Intrigue(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Intelligence(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Prowess(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Boldness(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Compassion(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Greed(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Honor(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Rationality(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Sociability(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Vengefulness(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            Luck(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )
        obj.add_component(
            RomancePropensity(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if options.randomize_stats else 0,
            )
        )

        db = world.get_resource(SimDB).db

        db.execute(
            """
            INSERT INTO characters
            (
                uid, first_name, surname, birth_surname,
                sex, sexual_orientation, life_stage, is_alive, age
            )
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

        # Sample personality traits
        trait_library = world.get_resource(TraitLibrary)

        personality_traits = trait_library.get_traits_with_tags(["personality"])

        for _ in range(options.n_max_personality_traits):

            potential_traits = [
                t
                for t in personality_traits
                if not has_conflicting_trait(obj, t) and not has_trait(obj, t.trait_id)
            ]

            traits: list[str] = []
            trait_weights: list[int] = []

            for trait in potential_traits:
                traits.append(trait.trait_id)
                trait_weights.append(1)

            if len(traits) == 0:
                continue

            chosen_trait = rng.choices(population=traits, weights=trait_weights, k=1)[0]

            add_trait(obj, chosen_trait)

        db.commit()

        return obj


def spawn_character(
    world: World, options: Optional[CharacterGenOptions] = None
) -> Entity:
    """Spawn a new character."""
    return world.get_resource(PCGFactories).character_factory.generate_character(
        world=world, options=options if options else CharacterGenOptions()
    )


def spawn_spouse_for(
    character: Entity, options: Optional[CharacterGenOptions] = None
) -> Entity:
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

    config = character.world.get_resource(Config)

    option_overrides = options if options else CharacterGenOptions()
    option_overrides.sex = spouse_sex
    option_overrides.n_max_personality_traits = config.max_personality_traits
    option_overrides.life_stage = character_component.life_stage

    return spawn_character(world=character.world, options=option_overrides)


def spawn_baby_from(
    mother: Entity, father: Entity, options: Optional[CharacterGenOptions] = None
) -> Entity:
    """Spawn a new baby given two parents."""
    return mother.world.get_resource(PCGFactories).baby_factory.generate_child(
        mother, father, options if options else CharacterGenOptions()
    )


class DefaultBabyFactory(BabyFactory):
    """Built-in implementation of a BabyFactory."""

    def generate_child(
        self, mother: Entity, father: Entity, options: CharacterGenOptions
    ) -> Entity:
        """Generate a child from the given parents."""
        rng = mother.world.get_resource(random.Random)
        config = mother.world.get_resource(Config)

        mother_character_component = mother.get_component(Character)

        mothers_family = mother_character_component.family
        assert mothers_family

        character_factory = mother.world.get_resource(PCGFactories).character_factory

        option_overrides = options
        option_overrides.age = 0
        option_overrides.n_max_personality_traits = 0
        option_overrides.surname = mothers_family.name

        child = character_factory.generate_character(
            world=mother.world,
            options=option_overrides,
        )

        set_character_birth_date(child, mother.world.get_resource(SimDate).copy())
        set_character_birth_surname(child, mothers_family.name)
        set_character_birth_family(child, mothers_family)
        set_character_family(child, mothers_family)

        # Replace personality traits with ones from parents
        mother_personality = get_personality_traits(mother)
        father_personality = get_personality_traits(father)

        all_parent_traits: list[Trait] = sorted(
            list(set(mother_personality).union(set(father_personality))),
            key=lambda t: t.trait_id,
        )

        for _ in range(config.n_personality_traits_from_parents):
            potential_traits = [
                t
                for t in all_parent_traits
                if not has_conflicting_trait(child, t)
                and not has_trait(child, t.trait_id)
            ]

            traits: list[str] = []
            trait_weights: list[int] = []

            for trait in potential_traits:
                traits.append(trait.trait_id)
                trait_weights.append(1)

            if len(traits) == 0:
                continue

            chosen_trait = rng.choices(population=traits, weights=trait_weights, k=1)[0]

            add_trait(child, chosen_trait)

        child_personality = get_personality_traits(child)

        n_additional_traits = config.max_personality_traits - len(child_personality)

        trait_library = mother.world.get_resource(TraitLibrary)

        personality_traits = trait_library.get_traits_with_tags(["personality"])

        for _ in range(n_additional_traits):
            potential_traits = [
                t
                for t in personality_traits
                if not has_conflicting_trait(child, t)
                and not has_trait(child, t.trait_id)
            ]

            traits: list[str] = []
            trait_weights: list[int] = []

            for trait in potential_traits:
                traits.append(trait.trait_id)
                trait_weights.append(1)

            if len(traits) == 0:
                continue

            chosen_trait = rng.choices(population=traits, weights=trait_weights, k=1)[0]

            add_trait(child, chosen_trait)

        return child


class DefaultFamilyFactory(FamilyFactory):
    """Built-in implementation of a FamilyFactory"""

    __slots__ = ("name_factory",)

    def __init__(self, name_factory: NameFactory) -> None:
        super().__init__()
        self.name_factory = name_factory

    def generate_family(self, world: World, options: FamilyGenOptions) -> Entity:
        """Create a new family."""
        rng = world.get_resource(random.Random)
        config = world.get_resource(Config)
        current_date = world.get_resource(SimDate)
        db = world.get_resource(SimDB).db

        family = world.entity()
        family_name = (
            options.name if options.name else self.name_factory.generate_name(family)
        )

        color_primary = rng.choice(config.family_colors_primary)
        color_secondary = rng.choice(config.family_colors_secondary)
        color_tertiary = rng.choice(config.family_colors_tertiary)
        banner_symbol = rng.choice(config.family_banner_symbols)

        family.add_component(
            Family(
                name=family_name,
                color_primary=color_primary,
                color_secondary=color_secondary,
                color_tertiary=color_tertiary,
                banner_symbol=banner_symbol,
            )
        )
        family.add_component(LifeEventHistory())
        family.add_component(WarTracker())
        family.add_component(FamilyPrestige(default_stat_calc_strategy))
        family.name = f"{family_name}"

        db.execute(
            """
            INSERT INTO families
            (uid, name, founding_date)
            VALUES (?, ?, ?);
            """,
            (family.uid, family.name, current_date.to_iso_str()),
        )

        db.commit()

        if options.spawn_members:
            self.fill_family(family)

        world.get_resource(SimulationEvents).family_added.emit(family)

        return family

    def fill_family(self, family: Entity) -> Entity:
        """Generates a family and its initial members."""
        world = family.world
        rng = world.get_resource(random.Random)
        config = world.get_resource(Config)

        # Create a new family
        family_surname = family.get_component(Family).name

        # Track the household heads that are generated. The head of the first
        # household will become the family head.
        household_heads: list[Entity] = []

        n_household_to_generate: int = rng.randint(1, config.max_households_per_family)

        for _ in range(n_household_to_generate):
            # Create a new household head
            household_head = spawn_character(
                world,
                CharacterGenOptions(
                    life_stage=LifeStage.YOUNG_ADULT,
                    sex=Sex.MALE,
                    sexual_orientation=SexualOrientation.HETEROSEXUAL,
                    n_max_personality_traits=config.max_personality_traits,
                ),
            )

            set_character_surname(household_head, family_surname)
            set_character_birth_surname(household_head, family_surname)

            household_heads.append(household_head)

            set_character_family(household_head, family)

            # Generate a spouse for the household head
            spouse = spawn_spouse_for(household_head)

            set_character_surname(spouse, family_surname)
            set_character_family(spouse, family)

            # Update the relationship between the household head and spouse
            start_marriage(household_head, spouse)

            n_children = rng.randint(0, config.max_children_per_household)

            generated_children: list[Entity] = []

            for _ in range(n_children):
                child = spawn_baby_from(spouse, household_head)

                set_character_surname(child, family_surname)

                set_character_family(child, family)
                set_character_birth_family(child, family)

                set_relation_child(household_head, child)
                set_relation_child(spouse, child)
                set_character_father(child, household_head)
                set_character_mother(child, spouse)
                set_character_biological_father(child, household_head)

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
        family.get_component(Family).founder = household_heads[0]

        return family


def spawn_family(world: World, options: Optional[FamilyGenOptions] = None) -> Entity:
    """Spawn a new character."""
    return world.get_resource(PCGFactories).family_factory.generate_family(
        world=world, options=options if options else FamilyGenOptions()
    )

"""Character Generation Classes and Functions."""

from __future__ import annotations

import random
from typing import Optional

from ordered_set import OrderedSet

from minerva.actions.base_types import AIBrain, AIContext, SchemeManager
from minerva.actions.behavior_helpers import (
    TerritoriesControlledByOpps,
    TerritoriesInRevoltSensor,
    UnControlledTerritoriesSensor,
    UnexpandedTerritoriesSensor,
    WeightedActionSelectStrategy,
    WeightedBehaviorSelectStrategy,
)
from minerva.characters.betrothal_data import BetrothalTracker
from minerva.characters.components import (
    Boldness,
    Character,
    Compassion,
    Diplomacy,
    DreadMotive,
    Family,
    FamilyMotive,
    Fertility,
    Greed,
    HappinessMotive,
    HeadOfFamily,
    Honor,
    HonorMotive,
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
    Species,
    SpeciesLibrary,
    Stewardship,
    Vengefulness,
    ViolencePropensity,
    WantForChildren,
    WantForMarriage,
    WantForPower,
    Zeal,
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
    set_family_home_base,
    set_relation_child,
    set_relation_sibling,
    start_marriage,
)
from minerva.characters.succession_helpers import set_current_ruler
from minerva.characters.war_data import WarTracker
from minerva.config import Config
from minerva.datetime import SimDate
from minerva.ecs import Active, Event, GameObject, World
from minerva.life_events.base_types import LifeEventHistory
from minerva.pcg.base_types import (
    BabyFactory,
    CharacterFactory,
    FamilyFactory,
    NameFactory,
    PCGFactories,
)
from minerva.relationships.base_types import RelationshipManager
from minerva.sim_db import SimDB
from minerva.stats.base_types import StatusEffectManager
from minerva.stats.helpers import default_stat_calc_strategy
from minerva.traits.base_types import Trait, TraitLibrary, TraitManager
from minerva.traits.helpers import (
    add_trait,
    get_personality_traits,
    has_conflicting_trait,
    has_trait,
)
from minerva.world_map.components import Territory
from minerva.world_map.helpers import set_territory_controlling_family


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
        self,
        world: World,
        *,
        first_name: str = "",
        surname: str = "",
        species: str = "",
        sex: Optional[Sex] = None,
        sexual_orientation: Optional[SexualOrientation] = None,
        life_stage: Optional[LifeStage] = None,
        age: Optional[int] = None,
        n_max_personality_traits: int = 0,
        randomize_stats: bool = True,
    ) -> GameObject:
        """Create a new character."""
        rng = world.resources.get_resource(random.Random)

        obj = world.gameobjects.spawn_gameobject()
        obj.metadata["object_type"] = "character"

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
                raise RuntimeError(
                    "No eligible species found for character generation."
                )

            chosen_species: Species = rng.choices(
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
        if first_name:
            chosen_first_name = first_name
        elif chosen_sex == Sex.MALE:
            chosen_first_name = self.male_first_name_factory.generate_name(obj)
        else:
            chosen_first_name = self.female_first_name_factory.generate_name(obj)

        # Step 4: Generate surname
        chosen_surname = surname if surname else self.surname_factory.generate_name(obj)

        # Step 5a: Generate an age and a life stage
        chosen_life_stage = rng.choice(list(LifeStage))
        chosen_age = self.generate_random_character_age(
            world,
            chosen_species,
            chosen_life_stage,
        )

        # Step 5b: Generate an age if given a life stage
        if life_stage is not None:
            chosen_life_stage = life_stage
            chosen_age = self.generate_random_character_age(
                world,
                chosen_species,
                chosen_life_stage,
            )

        # Step 5c: Generate a life state of given an age
        if age is not None:
            chosen_age = age
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
        obj.add_component(RelationshipManager())
        obj.add_component(LifeEventHistory())
        obj.add_component(MarriageTracker())
        obj.add_component(RomanticAffairTracker())
        obj.add_component(BetrothalTracker())
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
                action_selection_strategy=WeightedActionSelectStrategy(rng=rng),
                behavior_selection_strategy=WeightedBehaviorSelectStrategy(rng=rng),
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
        obj.add_component(Fertility(default_stat_calc_strategy, base_value=100))
        obj.add_component(
            Diplomacy(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Martial(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Stewardship(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Intrigue(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Learning(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Prowess(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Boldness(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Compassion(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Greed(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Honor(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Rationality(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Sociability(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Vengefulness(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Zeal(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            Luck(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            RomancePropensity(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            ViolencePropensity(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            WantForPower(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            WantForChildren(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
        obj.add_component(
            WantForMarriage(
                default_stat_calc_strategy,
                base_value=rng.randint(0, 80) if randomize_stats else 0,
            )
        )
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
        trait_library = world.resources.get_resource(TraitLibrary)

        personality_traits = trait_library.get_traits_with_tags(["personality"])

        for _ in range(n_max_personality_traits):

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

    character_factory = character.world.resources.get_resource(
        PCGFactories
    ).character_factory

    config = character.world.resources.get_resource(Config)

    return character_factory.generate_character(
        world=character.world,
        sex=spouse_sex,
        n_max_personality_traits=config.max_personality_traits,
    )


class DefaultBabyFactory(BabyFactory):
    """Built-in implementation of a BabyFactory."""

    def generate_child(self, mother: GameObject, father: GameObject) -> GameObject:
        """Generate a child from the given parents."""
        rng = mother.world.resources.get_resource(random.Random)
        config = mother.world.resources.get_resource(Config)

        mother_character_component = mother.get_component(Character)

        mothers_family = mother_character_component.family
        assert mothers_family

        character_factory = mother.world.resources.get_resource(
            PCGFactories
        ).character_factory

        child = character_factory.generate_character(
            world=mother.world,
            life_stage=LifeStage.CHILD,
            n_max_personality_traits=0,
            surname=mothers_family.name,
        )

        set_character_birth_date(
            child, mother.world.resources.get_resource(SimDate).copy()
        )
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

        trait_library = mother.world.resources.get_resource(TraitLibrary)

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

    def generate_family(self, world: World, name: str = "") -> GameObject:
        """Create a new family."""
        rng = world.resources.get_resource(random.Random)
        config = world.resources.get_resource(Config)
        current_date = world.resources.get_resource(SimDate)
        db = world.resources.get_resource(SimDB).db

        family = world.gameobjects.spawn_gameobject()
        family.metadata["object_type"] = "family"
        family_name = name if name else self.name_factory.generate_name(family)

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
        family.add_component(WarTracker())
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

        world.events.dispatch_event(
            Event(
                event_type="family-added",
                world=world,
                family=family,
            )
        )

        return family


def generate_initial_families(world: World) -> None:
    """Generates initial families."""

    # config = world.resources.get_resource(Config)
    rng = world.resources.get_resource(random.Random)

    # Generate the initial families
    _generate_initial_families(world)

    families = [
        world.gameobjects.get_gameobject(uid)
        for uid, _ in world.get_components((Family, Active))
    ]

    # Assign families to territories
    territories = [
        world.gameobjects.get_gameobject(uid)
        for uid, _ in world.get_components((Territory, Active))
    ]

    unassigned_families = [*families]
    rng.shuffle(unassigned_families)

    unassigned_territories = [*territories]

    # Designate a family as the royal family
    family_heads = [
        family_head.gameobject
        for _, (family_head, _) in world.get_components((HeadOfFamily, Active))
    ]

    # Start the first dynasty
    chosen_emperor = rng.choice(family_heads)
    set_current_ruler(world, chosen_emperor)

    emperor_family = chosen_emperor.get_component(Character).family
    assert emperor_family is not None, "Emperor family cannot be none"

    for family in OrderedSet([emperor_family, *families]):
        if unassigned_territories:
            home_base = unassigned_territories.pop()
            set_territory_controlling_family(home_base, family)
        else:
            home_base = rng.choice(territories)

        set_family_home_base(family, rng.choice(territories))
        family_component = family.get_component(Family)
        family_component.territories.add(home_base)


def _generate_initial_families(world: World) -> list[GameObject]:
    """Generate initial families."""
    rng = world.resources.get_resource(random.Random)
    config = world.resources.get_resource(Config)

    families: list[GameObject] = []

    family_factory = world.resources.get_resource(PCGFactories).family_factory
    character_factory = world.resources.get_resource(PCGFactories).character_factory
    baby_factory = world.resources.get_resource(PCGFactories).baby_factory

    for _ in range(config.n_initial_families):
        # Create a new family
        family = family_factory.generate_family(world)
        family_surname = family.get_component(Family).name
        families.append(family)

        # Track the household heads that are generated. The head of the first
        # household will become the family head.
        household_heads: list[GameObject] = []

        n_household_to_generate: int = rng.randint(1, config.max_households_per_family)

        for _ in range(n_household_to_generate):
            # Create a new household head
            household_head = character_factory.generate_character(
                world,
                life_stage=LifeStage.ADULT,
                sex=Sex.MALE,
                sexual_orientation=SexualOrientation.HETEROSEXUAL,
                n_max_personality_traits=config.max_personality_traits,
            )

            set_character_surname(household_head, family_surname)
            set_character_birth_surname(household_head, family_surname)

            household_heads.append(household_head)

            set_character_family(household_head, family)

            # Generate a spouse for the household head
            spouse = generate_spouse_for(household_head)

            set_character_surname(spouse, family_surname)
            set_character_family(spouse, family)

            # Update the relationship between the household head and spouse
            start_marriage(household_head, spouse)

            n_children = rng.randint(0, config.max_children_per_household)

            generated_children: list[GameObject] = []

            for _ in range(n_children):
                child = baby_factory.generate_child(spouse, household_head)

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

    return families

"""Minerva Base Systems."""

import random

from minerva.characters.components import (
    Character,
    Family,
    LifeStage,
    Sex,
    SexualOrientation,
    Fertility,
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
    set_clan_home_base,
    set_clan_name,
    set_family_clan,
    set_family_head,
    set_household_family,
    set_household_head,
    set_relation_child,
    set_relation_spouse,
    set_character_age, set_relation_sibling,
)
from minerva.config import WORLD_SIZE, Config
from minerva.datetime import SimDate, MONTHS_PER_YEAR
from minerva.ecs import Active, GameObject, System, World
from minerva.effects.base_types import EffectLibrary
from minerva.life_events.aging import (
    BecomeAdultEvent,
    BecomeYoungAdultEvent,
    BecomeAdolescentEvent,
    BecomeSeniorEvent,
)
from minerva.life_events.base_types import dispatch_life_event
from minerva.pcg.character import (
    generate_character,
    generate_child_from,
    generate_clan,
    generate_family,
    generate_household,
    generate_spouse_for,
)
from minerva.pcg.settlement import generate_settlement
from minerva.settlements.base_types import Settlement, WorldGrid
from minerva.settlements.helpers import set_settlement_controlling_clan
from minerva.stats.base_types import StatusEffect, StatusEffectManager
from minerva.stats.helpers import remove_status_effect
from minerva.traits.base_types import Trait, TraitLibrary


class CompileTraitDefsSystem(System):
    """Instantiates all the trait definitions within the TraitLibrary."""

    __system_group__ = "InitializationSystems"

    def on_update(self, world: World) -> None:
        trait_library = world.resources.get_resource(TraitLibrary)
        effect_library = world.resources.get_resource(EffectLibrary)

        # Add the new definitions and instances to the library.
        for trait_def in trait_library.definitions.values():
            trait = Trait(
                trait_id=trait_def.trait_id,
                name=trait_def.name,
                inheritance_chance_both=trait_def.inheritance_chance_both,
                inheritance_chance_single=trait_def.inheritance_chance_single,
                is_inheritable=(
                    trait_def.inheritance_chance_single > 0
                    or trait_def.inheritance_chance_both > 0
                ),
                description=trait_def.description,
                effects=[
                    effect_library.create_from_obj(
                        world, {"reason": f"Has {trait_def.name} trait", **entry}
                    )
                    for entry in trait_def.effects
                ],
                conflicting_traits=trait_def.conflicts_with,
            )

            trait_library.add_trait(trait)

        # Free up some memory
        trait_library.definitions.clear()


class TimeSystem(System):
    """Increments the current date/time."""

    __system_group__ = "LateUpdateSystems"
    __update_order__ = ("last",)

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate)

        current_date.increment_month()


class TickStatusEffectSystem(System):
    """Tick all status effects."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for uid, (status_effect_manager, _) in world.get_components(
            (StatusEffectManager, Active)
        ):
            gameobject = world.gameobjects.get_gameobject(uid)
            effects_to_remove: list[StatusEffect] = []

            for status_effect in status_effect_manager.status_effects:
                if status_effect.is_expired():
                    effects_to_remove.append(status_effect)
                else:
                    status_effect.update(gameobject)

            for status_effect in effects_to_remove:
                remove_status_effect(gameobject, status_effect)


class CharacterAgingSystem(System):
    """Age characters over time."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        # This system runs every simulated month
        elapsed_years: float = 1.0 / MONTHS_PER_YEAR

        for _, (character, fertility, _) in world.get_components(
            (Character, Fertility, Active)
        ):
            age = character.age + elapsed_years
            set_character_age(character.gameobject, age)

            # Check if they changed life stages
            species = character.species

            if species.can_physically_age:
                if age >= species.senior_age:
                    if character.life_stage != LifeStage.SENIOR:
                        fertility_max = (
                            species.senior_male_fertility
                            if character.sex == Sex.MALE
                            else species.senior_female_fertility
                        )

                        fertility.base_value = min(
                            fertility.base_value, fertility_max
                        )

                        evt = BecomeSeniorEvent(character.gameobject)
                        character.life_stage = LifeStage.SENIOR
                        dispatch_life_event(evt, [character.gameobject])

                elif age >= species.adult_age:
                    if character.life_stage != LifeStage.ADULT:
                        fertility_max = (
                            species.adult_male_fertility
                            if character.sex == Sex.MALE
                            else species.adult_female_fertility
                        )
                        fertility.base_value = min(
                            fertility.base_value, fertility_max
                        )

                        character.life_stage = LifeStage.ADULT
                        dispatch_life_event(
                            BecomeAdultEvent(character.gameobject),
                            [character.gameobject],
                        )

                elif age >= species.young_adult_age:
                    if character.life_stage != LifeStage.YOUNG_ADULT:
                        fertility_max = (
                            species.young_adult_male_fertility
                            if character.sex == Sex.MALE
                            else species.young_adult_female_fertility
                        )

                        fertility.base_value = min(
                            fertility.base_value, fertility_max
                        )

                        evt = BecomeYoungAdultEvent(character.gameobject)
                        character.life_stage = LifeStage.YOUNG_ADULT
                        dispatch_life_event(evt, [character.gameobject])

                elif age >= species.adolescent_age:
                    if character.life_stage != LifeStage.ADOLESCENT:
                        fertility_max = (
                            species.adolescent_male_fertility
                            if character.sex == Sex.MALE
                            else species.adolescent_female_fertility
                        )

                        fertility.base_value = min(
                            fertility.base_value, fertility_max
                        )

                        evt = BecomeAdolescentEvent(character.gameobject)
                        character.life_stage = LifeStage.ADOLESCENT
                        dispatch_life_event(evt, [character.gameobject])

                else:
                    if character.life_stage != LifeStage.CHILD:
                        character.life_stage = LifeStage.CHILD


class InitializeWorldMap(System):
    """Create the world map and settlements."""

    __system_group__ = "InitializationSystems"
    __update_order__ = ("first",)

    def on_update(self, world: World) -> None:
        config = world.resources.get_resource(Config)

        world_size = WORLD_SIZE[config.world_size]
        world_grid = WorldGrid(world_size)

        world.resources.add_resource(world_grid)

        for x in range(world_grid.n_cols):
            for y in range(world_grid.n_rows):
                settlement = generate_settlement(world)

                world_grid.set(x, y, settlement)


class InitializeClansSystem(System):
    """Create initial social landscape with multiple clans."""

    __system_group__ = "InitializationSystems"
    __update_order__ = ("last",)

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)
        clans = self.generate_clans(world)
        settlements = [
            world.gameobjects.get_gameobject(uid)
            for uid, _ in world.get_components((Settlement, Active))
        ]

        unassigned_clans = [*clans]
        rng.shuffle(unassigned_clans)

        unassigned_settlements = [*settlements]

        for clan in clans:
            if unassigned_settlements:
                home_base = unassigned_settlements.pop()
                set_settlement_controlling_clan(home_base, clan)
                set_clan_home_base(clan, home_base)

            home_base = rng.choice(settlements)
            set_clan_home_base(clan, home_base)

    @staticmethod
    def generate_clans(world: World) -> list[GameObject]:
        """Generate initial clans."""
        rng = world.resources.get_resource(random.Random)
        config = world.resources.get_resource(Config)

        clans: list[GameObject] = []

        # Spawn clans
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
                    set_relation_spouse(household_head, spouse)
                    set_relation_spouse(spouse, household_head)

                    # add_trait(
                    #     get_relationship(household_head, spouse),
                    #     "spouse",
                    # )
                    # add_trait(
                    #     get_relationship(spouse, household_head),
                    #     "spouse",
                    # )

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

                        # add_trait(
                        #     get_relationship(household_head, child),
                        #     "child",
                        # )
                        # add_trait(
                        #     get_relationship(spouse, child),
                        #     "child",
                        # )
                        #
                        # add_trait(
                        #     get_relationship(child, household_head),
                        #     "parent",
                        # )
                        # add_trait(
                        #     get_relationship(child, spouse),
                        #     "parent",
                        # )

                        # add_trait(
                        #     get_relationship(child, other_child),
                        #     "sibling",
                        # )
                        # add_trait(
                        #     get_relationship(other_child, child),
                        #     "sibling",
                        # )

                # Set the family head
                set_family_head(family, household_heads[0])
                family_heads.append(household_heads[0])

            # Set the clan head
            set_clan_head(clan, family_heads[0])
            set_clan_name(clan, family_heads[0].get_component(Character).surname)
            set_clan_name(clan, family_heads[0].get_component(Character).surname)

        return clans

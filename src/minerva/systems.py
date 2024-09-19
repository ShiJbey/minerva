"""Minerva Base Systems."""

import random

from ordered_set import OrderedSet

from minerva.actions.actions import Die
from minerva.actions.base_types import AIBehaviorLibrary, IAIBehavior
from minerva.actions.behavior_helpers import get_behavior_utility
from minerva.characters.components import (
    Character,
    Clan,
    Emperor,
    Family,
    FamilyRoleFlags,
    Fertility,
    HeadOfFamily,
    Lifespan,
    LifeStage,
    Sex,
)
from minerva.characters.helpers import (
    assign_family_member_to_roles,
    get_advisor_candidates,
    get_warrior_candidates,
    remove_clan_from_play,
    remove_family_from_play,
    set_character_age,
    set_clan_head,
    set_family_head,
)
from minerva.characters.motive_helpers import get_character_motives
from minerva.characters.succession_helpers import (
    SuccessionChartCache,
    get_succession_depth_chart,
    set_current_ruler,
)
from minerva.constants import (
    BEHAVIOR_UTILITY_THRESHOLD,
    MAX_ADVISORS_PER_FAMILY,
    MAX_WARRIORS_PER_FAMILY,
)
from minerva.datetime import MONTHS_PER_YEAR, SimDate
from minerva.ecs import Active, GameObject, System, World
from minerva.life_events.aging import LifeStageChangeEvent
from minerva.life_events.succession import BecameClanHeadEvent, BecameFamilyHeadEvent
from minerva.stats.base_types import StatusEffect, StatusEffectManager
from minerva.stats.helpers import remove_status_effect


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

            species = character.species

            if species.can_physically_age:
                if age >= species.senior_age:
                    if character.life_stage != LifeStage.SENIOR:
                        fertility_max = (
                            species.senior_male_fertility
                            if character.sex == Sex.MALE
                            else species.senior_female_fertility
                        )

                        fertility.base_value = min(fertility.base_value, fertility_max)

                        character.life_stage = LifeStage.SENIOR
                        LifeStageChangeEvent(
                            character.gameobject, LifeStage.SENIOR
                        ).dispatch()

                elif age >= species.adult_age:
                    if character.life_stage != LifeStage.ADULT:
                        fertility_max = (
                            species.adult_male_fertility
                            if character.sex == Sex.MALE
                            else species.adult_female_fertility
                        )
                        fertility.base_value = min(fertility.base_value, fertility_max)

                        character.life_stage = LifeStage.ADULT
                        LifeStageChangeEvent(
                            character.gameobject, LifeStage.ADULT
                        ).dispatch()

                elif age >= species.young_adult_age:
                    if character.life_stage != LifeStage.YOUNG_ADULT:
                        fertility_max = (
                            species.young_adult_male_fertility
                            if character.sex == Sex.MALE
                            else species.young_adult_female_fertility
                        )

                        fertility.base_value = min(fertility.base_value, fertility_max)

                        character.life_stage = LifeStage.YOUNG_ADULT
                        LifeStageChangeEvent(
                            character.gameobject, LifeStage.YOUNG_ADULT
                        ).dispatch()

                elif age >= species.adolescent_age:
                    if character.life_stage != LifeStage.ADOLESCENT:
                        fertility_max = (
                            species.adolescent_male_fertility
                            if character.sex == Sex.MALE
                            else species.adolescent_female_fertility
                        )

                        fertility.base_value = min(fertility.base_value, fertility_max)

                        character.life_stage = LifeStage.ADOLESCENT
                        LifeStageChangeEvent(
                            character.gameobject, LifeStage.ADOLESCENT
                        ).dispatch()

                else:
                    if character.life_stage != LifeStage.CHILD:
                        character.life_stage = LifeStage.CHILD

                        LifeStageChangeEvent(
                            character.gameobject, LifeStage.CHILD
                        ).dispatch()


class CharacterLifespanSystem(System):
    """Kills of characters who have reached their lifespan."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (character, life_span, _) in world.get_components(
            (Character, Lifespan, Active)
        ):
            if character.age >= life_span.value:
                Die(character.gameobject).execute()


class SuccessionDepthChartUpdateSystem(System):
    """Updates the succession depth chart for all family heads."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        chart_cache = world.resources.get_resource(SuccessionChartCache)

        for _, (character, _, _) in world.get_components(
            (Character, HeadOfFamily, Active)
        ):
            chart_cache.get_chart_for(character.gameobject, recalculate=True)


class FallbackFamilySuccessionSystem(System):
    """Appoint oldest person as head of a family after a failed succession."""

    __system_group__ = "LateUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (family, _) in world.get_components((Family, Active)):
            if family.head is not None:
                continue

            eligible_members: list[Character] = []

            for m in family.active_members:
                character_component = m.get_component(Character)
                if (
                    character_component.is_alive
                    and character_component.birth_family == family.gameobject
                    and character_component.life_stage > LifeStage.CHILD
                ):
                    eligible_members.append(character_component)

            eligible_members.sort(key=lambda _m: _m.age)

            if eligible_members:
                oldest_member = eligible_members[-1]
                set_family_head(family.gameobject, oldest_member.gameobject)
                BecameFamilyHeadEvent(
                    oldest_member.gameobject, family.gameobject
                ).dispatch()


class FallbackClanSuccessionSystem(System):
    """Appoint oldest family head as the new clan head."""

    __system_group__ = "LateUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (clan, _) in world.get_components((Clan, Active)):
            if clan.head is not None:
                continue

            eligible_heads: list[Character] = []

            for m in clan.members:
                character_component = m.get_component(Character)

                if not m.has_component(HeadOfFamily):
                    continue

                if (
                    character_component.is_alive
                    and character_component.life_stage > LifeStage.CHILD
                ):
                    eligible_heads.append(character_component)

            eligible_heads.sort(key=lambda _m: _m.age)

            if eligible_heads:
                oldest_member = eligible_heads[-1]
                set_clan_head(clan.gameobject, oldest_member.gameobject)
                BecameClanHeadEvent(
                    oldest_member.gameobject, clan.gameobject
                ).dispatch()


class FallbackEmperorSuccessionSystem(System):
    """If no emperor exists select one of the clan heads."""

    __system_group__ = "LateUpdateSystems"

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)

        emperor_exists = len(world.get_components((Emperor, Active))) > 0

        if emperor_exists:
            return

        eligible_clan_heads: list[GameObject] = []
        for _, (clan, _) in world.get_components((Clan, Active)):
            if clan.head is not None:
                eligible_clan_heads.append(clan.gameobject)

        if eligible_clan_heads:
            chosen_emperor = rng.choice(eligible_clan_heads)
            set_current_ruler(world, chosen_emperor)


class EmptyFamilyCleanUpSystem(System):
    """Removes empty families from play.

    Also removes empty clans if the family removed was the last within the clan.
    """

    __system_group__ = "LateUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (family, _) in world.get_components((Family, Active)):
            if len(family.active_members) == 0:
                remove_family_from_play(family.gameobject)


class EmptyClanCleanUpSystem(System):
    """Removes empty clans from play."""

    __system_group__ = "LateUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (clan, _) in world.get_components((Clan, Active)):
            if len(clan.active_families) == 0:
                remove_clan_from_play(clan.gameobject)


class CharacterBehaviorSystem(System):
    """Family heads and those high on the depth chart take actions."""

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)
        behavior_library = world.resources.get_resource(AIBehaviorLibrary)

        family_heads = [
            world.gameobjects.get_gameobject(uid)
            for uid, _ in world.get_components((HeadOfFamily, Active))
        ]

        all_acting_characters: OrderedSet[GameObject] = OrderedSet([*family_heads])

        for head in family_heads:
            depth_chart = get_succession_depth_chart(head)
            eligible_character_ids = [
                entry.character_id for entry in depth_chart if entry.is_eligible
            ]
            for uid in eligible_character_ids[:5]:
                all_acting_characters.add(world.gameobjects.get_gameobject(uid))

        acting_order = list(all_acting_characters)
        rng.shuffle(acting_order)

        for character in acting_order:
            if character.is_active:
                character_motives = get_character_motives(character)
                potential_behaviors: list[IAIBehavior] = []
                behavior_scores: list[float] = []
                for behavior in behavior_library.iter_behaviors():
                    if behavior.passes_preconditions(character):
                        _, utility = get_behavior_utility(character_motives, behavior)
                        if utility >= BEHAVIOR_UTILITY_THRESHOLD:
                            potential_behaviors.append(behavior)
                            behavior_scores.append(utility)

                if behavior_scores:
                    selected_behavior = rng.choices(
                        potential_behaviors, behavior_scores, k=1
                    )[0]

                    selected_behavior.execute(character)


class FamilyRoleSystem(System):
    """Automatically assign family members to empty family roles."""

    __system_group__ = "LateUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (family_component, _) in world.get_components((Family, Active)):
            # Fill advisor positions
            if len(family_component.advisors) < MAX_ADVISORS_PER_FAMILY:
                candidates = get_advisor_candidates(family_component.gameobject)
                if candidates:
                    seats_to_assign = min(
                        MAX_ADVISORS_PER_FAMILY - len(family_component.advisors),
                        len(candidates),
                    )

                    chosen_candidates = candidates[:seats_to_assign]

                    for family_member in chosen_candidates:
                        assign_family_member_to_roles(
                            family_component.gameobject,
                            family_member,
                            FamilyRoleFlags.ADVISOR,
                        )

            # Fill warrior positions
            if len(family_component.warriors) < MAX_WARRIORS_PER_FAMILY:
                candidates = get_warrior_candidates(family_component.gameobject)
                if candidates:
                    seats_to_assign = min(
                        MAX_WARRIORS_PER_FAMILY - len(family_component.warriors),
                        len(candidates),
                    )

                    chosen_candidates = candidates[:seats_to_assign]

                    for family_member in chosen_candidates:
                        assign_family_member_to_roles(
                            family_component.gameobject,
                            family_member,
                            FamilyRoleFlags.WARRIOR,
                        )

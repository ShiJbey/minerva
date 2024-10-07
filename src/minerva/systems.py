"""Minerva Base Systems."""

import logging
import random
from typing import Callable, ClassVar, Optional

from ordered_set import OrderedSet

from minerva import constants
from minerva.actions.actions import Die
from minerva.actions.base_types import AIBehaviorLibrary, IAIBehavior
from minerva.actions.behavior_helpers import get_behavior_utility
from minerva.characters.components import (
    Character,
    Diplomacy,
    DynastyTracker,
    Emperor,
    Family,
    FamilyRoleFlags,
    Fertility,
    HeadOfFamily,
    Lifespan,
    LifeStage,
    Marriage,
    Pregnancy,
    Sex,
    SexualOrientation,
)
from minerva.characters.helpers import (
    assign_family_member_to_roles,
    get_advisor_candidates,
    get_warrior_candidates,
    merge_family_with,
    remove_family_from_play,
    set_character_age,
    set_character_biological_father,
    set_character_birth_family,
    set_character_family,
    set_character_father,
    set_character_mother,
    set_family_head,
    set_relation_child,
    set_relation_sibling,
    start_marriage,
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
from minerva.life_events.events import (
    BornEvent,
    GiveBirthEvent,
    MarriageEvent,
    PregnancyEvent,
    TakeOverProvinceEvent,
)
from minerva.life_events.succession import BecameFamilyHeadEvent
from minerva.pcg.character import generate_child_from
from minerva.stats.base_types import StatusEffect, StatusEffectManager
from minerva.stats.helpers import remove_status_effect
from minerva.world_map.components import InRevolt, PopulationHappiness, Settlement
from minerva.world_map.helpers import set_settlement_controlling_family

_logger = logging.getLogger(__name__)


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

            else:
                remove_family_from_play(family.gameobject)


class FallbackEmperorSuccessionSystem(System):
    """If no emperor exists select one of the family heads."""

    __system_group__ = "LateUpdateSystems"

    def on_update(self, world: World) -> None:
        dynasty_tracker = world.resources.get_resource(DynastyTracker)
        rng = world.resources.get_resource(random.Random)

        if dynasty_tracker.current_dynasty is not None:
            return

        eligible_family_heads: list[GameObject] = []
        for _, (family, _) in world.get_components((Family, Active)):
            if family.head is not None:
                eligible_family_heads.append(family.head)

        if eligible_family_heads:
            chosen_emperor = rng.choice(eligible_family_heads)
            set_current_ruler(world, chosen_emperor)


class EmptyFamilyCleanUpSystem(System):
    """Removes empty families from play."""

    __system_group__ = "LateUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (family, _) in world.get_components((Family, Active)):
            if len(family.active_members) == 0:
                remove_family_from_play(family.gameobject)


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


class SettlementRevoltSystem(System):
    """Settlements revolt against controlling family.

    When a settlement's happiness drops below a given threshold, the settlement will
    move into a revolt to remove the controlling family.

    """

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate)

        for _, (settlement, happiness, _) in world.get_components(
            (Settlement, PopulationHappiness, Active)
        ):
            # Ignore settlements with happiness over the threshold
            if happiness.value > constants.REVOLT_THRESHOLD:
                continue

            # Ignore settlements that are already revolting
            if settlement.gameobject.has_component(InRevolt):
                continue

            # Ignore settlements that are not controlled by a family
            if settlement.controlling_family is None:
                continue

            settlement.gameobject.add_component(InRevolt(start_date=current_date))

            _logger.info(
                "[%s]: %s is revolting.",
                current_date.to_iso_str(),
                settlement.gameobject.name_with_uid,
            )


class RevoltUpdateSystem(System):
    """Updates existing revolts."""

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate)

        for _, (settlement, happiness, in_revolt, _) in world.get_components(
            (Settlement, PopulationHappiness, InRevolt, Active)
        ):
            elapsed_months = (current_date - in_revolt.start_date).total_months

            # Ignore settlements that have not reached the point of no return
            if elapsed_months < constants.MONTHS_TO_QUELL_REBELLION:
                continue

            if settlement.controlling_family is None:
                settlement.gameobject.remove_component(InRevolt)
                happiness.base_value = constants.BASE_SETTLEMENT_HAPPINESS
                continue

            controlling_family_component = settlement.controlling_family.get_component(
                Family
            )
            if family_head := controlling_family_component.head:
                character_component = family_head.get_component(Character)
                character_component.influence_points -= 500

            settlement.gameobject.remove_component(InRevolt)
            happiness.base_value = constants.BASE_SETTLEMENT_HAPPINESS

            _logger.info(
                "[%s]: %s has removed the %s family from power.",
                current_date.to_iso_str(),
                settlement.gameobject.name_with_uid,
                settlement.controlling_family.name_with_uid,
            )

            # Remove the current family from power
            set_settlement_controlling_family(settlement.gameobject, None)


class SettlementRandomEventSystem(System):
    """Random events can happen to settlements to change their happiness.

    Outside of the actions of the controlling family, settlements can be subject
    to various random events that affect their happiness state. We select from them
    each month like a deck of cards.

    """

    __system_group__ = "UpdateSystems"

    _random_events: ClassVar[dict[str, tuple[float, Callable[[GameObject], None]]]] = {}

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)

        for _, (settlement, _) in world.get_components((Settlement, Active)):
            if settlement.controlling_family is None:
                continue

            event_name = self.choose_random_event(rng)

            if event_name is None:
                continue

            event_fn = self._random_events[event_name][1]

            event_fn(settlement.gameobject)

    def choose_random_event(self, rng: random.Random) -> Optional[str]:
        """Choose an event at random"""

        if not self._random_events:
            return None

        options: list[str] = []
        weights: list[float] = []

        for name, (weight, _) in self._random_events.items():
            options.append(name)
            weights.append(weight)

        choice = rng.choices(options, weights=weights, k=1)[0]

        return choice

    @classmethod
    def random_event(cls, name: str, relative_frequency: float):
        """Decorator for making random events."""

        def wrapper(fn: Callable[[GameObject], None]):
            if relative_frequency <= 0:
                raise ValueError("Relative frequency must be greater than 0")

            cls._random_events[name] = (relative_frequency, fn)

        return wrapper


@SettlementRandomEventSystem.random_event("nothing", 10)
def nothing_event(_: GameObject) -> None:
    """Do Nothing."""
    return


@SettlementRandomEventSystem.random_event("poor harvest", 0.5)
def poor_harvest_event(settlement: GameObject) -> None:
    """Poor harvest."""
    current_date = settlement.world.resources.get_resource(SimDate)
    happiness_component = settlement.get_component(PopulationHappiness)

    happiness_component.base_value -= 10

    _logger.info(
        "[%s]: %s has suffered a poor harvest.",
        current_date.to_iso_str(),
        settlement.name_with_uid,
    )


@SettlementRandomEventSystem.random_event("disease", 0.5)
def disease_event(settlement: GameObject) -> None:
    """Do Nothing."""
    current_date = settlement.world.resources.get_resource(SimDate)
    happiness_component = settlement.get_component(PopulationHappiness)

    happiness_component.base_value -= 10

    _logger.info(
        "[%s]: %s has suffered a disease outbreak.",
        current_date.to_iso_str(),
        settlement.name_with_uid,
    )


@SettlementRandomEventSystem.random_event("bountiful harvest", 0.5)
def bountiful_harvest_event(settlement: GameObject) -> None:
    """Do Nothing."""
    current_date = settlement.world.resources.get_resource(SimDate)
    happiness_component = settlement.get_component(PopulationHappiness)

    happiness_component.base_value += 10

    _logger.info(
        "[%s]: %s had a bountiful harvest.",
        current_date.to_iso_str(),
        settlement.name_with_uid,
    )


class InfluencePointGainSystem(System):
    """Increases the influence points for characters."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (character, _) in world.get_components((Character, Active)):
            influence_gain: int = 1

            if character.gameobject.has_component(Emperor):
                influence_gain += 5

            if character.gameobject.has_component(HeadOfFamily):
                influence_gain += 5

            diplomacy = character.gameobject.get_component(Diplomacy)
            diplomacy_score = int(diplomacy.value)
            if diplomacy_score > 0:
                influence_gain += diplomacy_score // 4

            character.influence_points = min(
                character.influence_points + influence_gain,
                constants.INFLUENCE_POINTS_MAX,
            )

            character.influence_points = max(0, character.influence_points)

            _logger.debug(
                "[%s]: %s has %d influence points",
                world.resources.get_resource(SimDate).to_iso_str(),
                character.gameobject.name_with_uid,
                character.influence_points,
            )


class ProvinceInfluencePointBoostSystem(System):
    """The head of a family that controls a province gets a influence point increase."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (province, _) in world.get_components((Settlement, Active)):
            if province.controlling_family is None:
                continue

            family_component = province.controlling_family.get_component(Family)

            if family_component.head is None:
                continue

            head_character_component = family_component.head.get_component(Character)

            head_character_component.influence_points += 10


class PlaceholderMarriageSystem(System):
    """This system marries has characters get married as soon as they become adults."""

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)
        chance_get_married = 1.0 / 12.0
        for _, (character, _) in world.get_components((Character, Active)):
            if character.spouse:
                continue

            if character.life_stage < LifeStage.YOUNG_ADULT:
                continue

            if character.sexual_orientation == SexualOrientation.ASEXUAL:
                continue

            if not rng.random() < chance_get_married:
                continue

            eligible_singles: list[Character] = []

            if (
                character.sexual_orientation == SexualOrientation.HETEROSEXUAL
                and character.sex == Sex.MALE
            ):
                # Looking for heterosexual or bisexual women
                eligible_singles = [
                    c
                    for _, (c, _) in world.get_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and c.sex == Sex.FEMALE
                    and (
                        c.sexual_orientation == SexualOrientation.HETEROSEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                    )
                    and c.gameobject not in character.siblings
                    and c.gameobject != character.mother
                    and c.gameobject != character.father
                    and c.gameobject != character.biological_father
                    and c.gameobject not in character.children
                    and c != character
                ]

            if (
                character.sexual_orientation == SexualOrientation.HETEROSEXUAL
                and character.sex == Sex.FEMALE
            ):
                # Looking for heterosexual or bisexual men
                eligible_singles = [
                    c
                    for _, (c, _) in world.get_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and c.sex == Sex.MALE
                    and (
                        c.sexual_orientation == SexualOrientation.HETEROSEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                    )
                    and c.gameobject not in character.siblings
                    and c.gameobject != character.mother
                    and c.gameobject != character.father
                    and c.gameobject != character.biological_father
                    and c.gameobject not in character.children
                    and c != character
                ]

            if (
                character.sexual_orientation == SexualOrientation.HOMOSEXUAL
                and character.sex == Sex.MALE
            ):
                # Looking for homosexual or bisexual men
                eligible_singles = [
                    c
                    for _, (c, _) in world.get_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and c.sex == Sex.MALE
                    and (
                        c.sexual_orientation == SexualOrientation.HOMOSEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                    )
                    and c.gameobject not in character.siblings
                    and c.gameobject != character.mother
                    and c.gameobject != character.father
                    and c.gameobject != character.biological_father
                    and c.gameobject not in character.children
                    and c != character
                ]

            if (
                character.sexual_orientation == SexualOrientation.HOMOSEXUAL
                and character.sex == Sex.FEMALE
            ):
                # Looking for homosexual or bisexual women
                eligible_singles = [
                    c
                    for _, (c, _) in world.get_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and c.sex == Sex.FEMALE
                    and (
                        c.sexual_orientation == SexualOrientation.HOMOSEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                    )
                    and c.gameobject not in character.siblings
                    and c.gameobject != character.mother
                    and c.gameobject != character.father
                    and c.gameobject != character.biological_father
                    and c.gameobject not in character.children
                    and c != character
                ]

            if (
                character.sexual_orientation == SexualOrientation.BISEXUAL
                and character.sex == Sex.MALE
            ):
                # Looking for homosexual or bisexual men
                eligible_singles = [
                    c
                    for _, (c, _) in world.get_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and c.sex == Sex.MALE
                    and (
                        c.sexual_orientation == SexualOrientation.HOMOSEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                    )
                    and c.gameobject not in character.siblings
                    and c.gameobject != character.mother
                    and c.gameobject != character.father
                    and c.gameobject != character.biological_father
                    and c.gameobject not in character.children
                    and c != character
                ]

            if (
                character.sexual_orientation == SexualOrientation.BISEXUAL
                and character.sex == Sex.FEMALE
            ):
                # Looking for homosexual or bisexual women
                eligible_singles = [
                    c
                    for _, (c, _) in world.get_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and c.sex == Sex.FEMALE
                    and (
                        c.sexual_orientation == SexualOrientation.HOMOSEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                    )
                    and c.gameobject not in character.siblings
                    and c.gameobject != character.mother
                    and c.gameobject != character.father
                    and c.gameobject != character.biological_father
                    and c.gameobject not in character.children
                    and c != character
                ]

            if not eligible_singles:
                continue

            new_spouse = rng.choice(eligible_singles)

            start_marriage(
                character_a=character.gameobject, character_b=new_spouse.gameobject
            )

            # Now handle any family logistics

            # Case 1: The character is head of their family and their new spouse is
            # the head of their family
            if character.gameobject.has_component(
                HeadOfFamily
            ) and new_spouse.gameobject.has_component(HeadOfFamily):
                # Join the families into a single entity
                family_a = character.family
                family_b = new_spouse.family
                assert family_a is not None
                assert family_b is not None
                set_family_head(family_b, None)
                merge_family_with(family_b, family_a)

            # Case 2: The character is head of their family and their spouse is not
            if character.gameobject.has_component(
                HeadOfFamily
            ) and not new_spouse.gameobject.has_component(HeadOfFamily):
                family_a = character.family
                assert family_a is not None
                set_character_family(new_spouse.gameobject, family_a)

            # Case 3: The character is not head of their family and their spouse is
            if not character.gameobject.has_component(
                HeadOfFamily
            ) and new_spouse.gameobject.has_component(HeadOfFamily):
                family_a = character.family
                family_b = new_spouse.family
                assert family_a is not None
                assert family_b is not None
                set_family_head(family_b, None)
                set_character_family(new_spouse.gameobject, family_a)

            # Case 4: Neither character is head of their family.
            if not character.gameobject.has_component(
                HeadOfFamily
            ) and not new_spouse.gameobject.has_component(HeadOfFamily):
                family_a = character.family
                assert family_a is not None
                set_character_family(new_spouse.gameobject, family_a)

            MarriageEvent(character.gameobject, new_spouse.gameobject).dispatch()
            MarriageEvent(new_spouse.gameobject, character.gameobject).dispatch()


class PregnancyPlaceHolderSystem(System):
    """Handles some subset of married couples having children."""

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)
        current_date = world.resources.get_resource(SimDate)
        due_date = current_date.copy()
        due_date.increment(months=9)

        for _, (marriage, _) in world.get_components((Marriage, Active)):
            character = marriage.character.get_component(Character)
            spouse = marriage.spouse.get_component(Character)

            if not (character.sex == Sex.FEMALE and spouse.sex == Sex.FEMALE):
                continue

            if character.gameobject.has_component(Pregnancy):
                continue

            character_fertility_comp = marriage.character.get_component(Fertility)
            character_fertility = character_fertility_comp.value / 100.0

            spouse_fertility_comp = marriage.spouse.get_component(Fertility)
            spouse_fertility = spouse_fertility_comp.value / 100.0

            chance_have_child = character_fertility * spouse_fertility

            if not rng.random() < chance_have_child:
                continue

            # Add pregnancy component to character
            character.gameobject.add_component(
                Pregnancy(
                    assumed_father=spouse.gameobject,
                    actual_father=spouse.gameobject,
                    conception_date=current_date.copy(),
                    due_date=due_date.copy(),
                )
            )

            character_fertility_comp.base_value -= 0.2

            PregnancyEvent(character.gameobject).dispatch()


class ChildBirthSystem(System):
    """Spawns new children when pregnant characters reach their due dates."""

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate)

        for _, (character, pregnancy, fertility, _) in world.get_components(
            (Character, Pregnancy, Fertility, Active)
        ):
            if pregnancy.due_date > current_date:
                continue

            father = pregnancy.actual_father

            baby = generate_child_from(
                mother=character.gameobject,
                father=father,
            )

            set_character_mother(baby, character.gameobject)
            set_character_father(baby, pregnancy.assumed_father)
            set_character_biological_father(baby, pregnancy.actual_father)

            # Add to mothers family
            set_character_family(baby, character.family)
            set_character_birth_family(baby, character.family)

            # Mother to child
            set_relation_child(character.gameobject, baby)

            # Father to child
            if pregnancy.assumed_father:
                set_relation_child(pregnancy.assumed_father, baby)

            # Create relationships with children of birthing parent
            for existing_child in character.children:
                if existing_child == baby:
                    continue

                set_relation_sibling(baby, existing_child)
                set_relation_sibling(existing_child, baby)

            # Create relationships with children of other parent
            for existing_child in father.children:
                if existing_child == baby:
                    continue

                set_relation_sibling(baby, existing_child)
                set_relation_sibling(existing_child, baby)

            character.gameobject.remove_component(Pregnancy)

            # Reduce the character's fertility according to their species
            fertility.base_value -= character.species.fertility_cost_per_child

            GiveBirthEvent(
                character=character.gameobject,
                child=baby,
            ).dispatch()

            BornEvent(
                character=baby,
            ).dispatch()


class TakeOverProvincePlaceholderSystem(System):
    """Automatically selects a family to take over a province based on influence."""

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)
        for _, (province, _) in world.get_components((Settlement, Active)):
            if province.controlling_family is not None:
                continue

            max_influence_points = -1

            for influence_points in province.political_influence.values():
                if influence_points > max_influence_points:
                    max_influence_points = influence_points

            eligible_families: list[GameObject] = []

            for family, influence_points in province.political_influence.items():
                family_component = family.get_component(Family)
                if (
                    influence_points == max_influence_points
                    and family_component.head is not None
                ):
                    eligible_families.append(family)

            if eligible_families:
                chosen_family = rng.choice(eligible_families)
                family_component = chosen_family.get_component(Family)
                set_settlement_controlling_family(province.gameobject, chosen_family)
                assert family_component.head is not None
                TakeOverProvinceEvent(
                    character=family_component.head,
                    province=province.gameobject,
                    family=chosen_family,
                ).dispatch()

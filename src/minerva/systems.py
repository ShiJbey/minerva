# pylint: disable=C0302
"""Minerva Base Systems."""

import logging
import random
from typing import Callable, ClassVar, Optional

from ordered_set import OrderedSet

from minerva.actions.actions import CheatOnSpouseAction, DieAction, SexAction
from minerva.actions.base_types import AIAction, AIBehaviorLibrary, AIBrain, Scheme
from minerva.actions.scheme_helpers import destroy_scheme
from minerva.actions.scheme_types import (
    AllianceScheme,
    CheatingScheme,
    CoupScheme,
    WarScheme,
)
from minerva.characters.components import (
    Character,
    Diplomacy,
    DynastyTracker,
    Emperor,
    Family,
    FamilyPrestige,
    FamilyRoleFlags,
    Fertility,
    HeadOfFamily,
    Intrigue,
    Lifespan,
    LifeStage,
    Marriage,
    Pregnancy,
    Prowess,
    Sex,
    SexualOrientation,
)
from minerva.characters.helpers import (
    assign_family_member_to_roles,
    get_advisor_candidates,
    get_family_of,
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
    set_family_home_base,
    set_relation_child,
    set_relation_sibling,
    start_marriage,
    update_grandparent_relations, set_character_life_stage, )
from minerva.characters.metric_data import CharacterMetrics
from minerva.characters.stat_helpers import StatLevel, get_luck_level
from minerva.characters.succession_helpers import (
    SuccessionChartCache,
    get_current_ruler,
    get_succession_depth_chart,
    remove_heir,
    set_current_ruler, set_heir,
)
from minerva.characters.war_data import Alliance, War, WarRole
from minerva.characters.war_helpers import (
    calculate_aggressor_win_probability,
    calculate_war_score,
    calculate_warrior_prowess_dist,
    destroy_alliance_scheme,
    destroy_coup_scheme,
    destroy_war_scheme,
    end_war,
    get_casualty_chance,
    join_war_as,
    start_alliance,
    start_war,
)
from minerva.config import Config
from minerva.datetime import MONTHS_PER_YEAR, SimDate
from minerva.ecs import Active, GameObject, System, SystemGroup, World
from minerva.life_events.aging import LifeStageChangeEvent
from minerva.life_events.events import (
    AllianceFoundedEvent,
    AllianceSchemeFailedEvent,
    BirthEvent,
    ChildBirthEvent,
    CoupSchemeDiscoveredEvent,
    DeclareWarEvent,
    DefendingTerritoryEvent,
    LostTerritoryEvent,
    MarriageEvent,
    PregnancyEvent,
    RemovedFromPowerEvent,
    RevoltEvent,
    RuleOverthrownEvent,
    SentencedToDeathEvent,
    UsurpEvent,
)
from minerva.life_events.succession import BecameFamilyHeadEvent
from minerva.pcg.base_types import PCGFactories
from minerva.pcg.character import generate_family
from minerva.relationships.base_types import Attraction, Opinion
from minerva.relationships.helpers import get_relationship
from minerva.stats.base_types import StatusEffect, StatusEffectManager
from minerva.stats.helpers import remove_status_effect
from minerva.world_map.components import InRevolt, PopulationHappiness, Territory
from minerva.world_map.helpers import set_territory_controlling_family

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

                        set_character_life_stage(character.gameobject, LifeStage.SENIOR)

                        LifeStageChangeEvent(
                            character.gameobject, LifeStage.SENIOR
                        ).log_event()

                elif age >= species.adult_age:
                    if character.life_stage != LifeStage.ADULT:
                        fertility_max = (
                            species.adult_male_fertility
                            if character.sex == Sex.MALE
                            else species.adult_female_fertility
                        )
                        fertility.base_value = min(fertility.base_value, fertility_max)

                        set_character_life_stage(character.gameobject, LifeStage.ADULT)

                        LifeStageChangeEvent(
                            character.gameobject, LifeStage.ADULT
                        ).log_event()

                elif age >= species.young_adult_age:
                    if character.life_stage != LifeStage.YOUNG_ADULT:
                        fertility_max = (
                            species.young_adult_male_fertility
                            if character.sex == Sex.MALE
                            else species.young_adult_female_fertility
                        )

                        fertility.base_value = min(fertility.base_value, fertility_max)

                        set_character_life_stage(character.gameobject, LifeStage.YOUNG_ADULT)

                        LifeStageChangeEvent(
                            character.gameobject, LifeStage.YOUNG_ADULT
                        ).log_event()

                elif age >= species.adolescent_age:
                    if character.life_stage != LifeStage.ADOLESCENT:
                        fertility_max = (
                            species.adolescent_male_fertility
                            if character.sex == Sex.MALE
                            else species.adolescent_female_fertility
                        )

                        fertility.base_value = min(fertility.base_value, fertility_max)

                        set_character_life_stage(character.gameobject, LifeStage.ADOLESCENT)

                        LifeStageChangeEvent(
                            character.gameobject, LifeStage.ADOLESCENT
                        ).log_event()

                else:
                    if character.life_stage != LifeStage.CHILD:
                        character.life_stage = LifeStage.CHILD

                        set_character_life_stage(character.gameobject, LifeStage.CHILD)

                        LifeStageChangeEvent(
                            character.gameobject, LifeStage.CHILD
                        ).log_event()


class CharacterLifespanSystem(System):
    """Kills of characters who have reached their lifespan."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (character, life_span, _) in world.get_components(
            (Character, Lifespan, Active)
        ):
            if character.age >= life_span.value:
                DieAction(character.gameobject, cause_of_death="old age").execute()


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

            former_head = family.former_heads[-1]

            depth_chart = get_succession_depth_chart(former_head)

            if len(depth_chart) > 0:
                heir_id = depth_chart[-1].character_id
                heir = world.gameobjects.get_gameobject(heir_id)
                set_family_head(family.gameobject, heir)
                BecameFamilyHeadEvent(heir, family.gameobject).log_event()
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
                actions: list[AIAction] = []
                character_component = character.get_component(Character)
                brain = character.get_component(AIBrain)
                brain.context.update_sensors()

                for behavior in behavior_library.iter_behaviors():
                    if behavior.passes_preconditions(character):
                        for potential_action in behavior.get_actions(character):
                            if (
                                brain.action_cooldowns[potential_action.get_name()] <= 0
                                and character_component.influence_points
                                >= potential_action.get_cost()
                            ):
                                # if potential_action.get_name() == "StartCoupScheme":
                                #     utility = potential_action.calculate_utility()
                                #     _logger.info(
                                #         "D:: [%s] Coup Scheme => %s",
                                #         character.uid,
                                #         utility,
                                #     )

                                # if potential_action.get_name() == "StartWarScheme":
                                #     utility = potential_action.calculate_utility()
                                #     _logger.info(
                                #         "D:: [%s] War Scheme => %s",
                                #         character.uid,
                                #         utility,
                                #     )

                                actions.append(potential_action)

                if len(actions) > 0:
                    selected_action = brain.action_selection_strategy.choose_action(
                        actions
                    )

                    brain.action_cooldowns[selected_action.get_name()] = (
                        selected_action.get_cooldown_time()
                    )

                    success = selected_action.execute()

                    if success:
                        character_component.influence_points -= (
                            selected_action.get_cost()
                        )

                brain.context.clear_blackboard()


class FamilyRoleSystem(System):
    """Automatically assign family members to empty family roles."""

    __system_group__ = "LateUpdateSystems"

    def on_update(self, world: World) -> None:
        config = world.resources.get_resource(Config)
        for _, (family_component, _) in world.get_components((Family, Active)):
            # Fill advisor positions
            if len(family_component.advisors) < config.max_advisors_per_family:
                candidates = get_advisor_candidates(family_component.gameobject)
                if candidates:
                    seats_to_assign = min(
                        config.max_advisors_per_family - len(family_component.advisors),
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
            if len(family_component.warriors) < config.max_warriors_per_family:
                candidates = get_warrior_candidates(family_component.gameobject)
                if candidates:
                    seats_to_assign = min(
                        config.max_warriors_per_family - len(family_component.warriors),
                        len(candidates),
                    )

                    chosen_candidates = candidates[:seats_to_assign]

                    for family_member in chosen_candidates:
                        assign_family_member_to_roles(
                            family_component.gameobject,
                            family_member,
                            FamilyRoleFlags.WARRIOR,
                        )


class TerritoryRevoltSystem(System):
    """Territories revolt against controlling family.

    When a territory's happiness drops below a given threshold, the territory will
    move into a revolt to remove the controlling family.

    """

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate)
        config = world.resources.get_resource(Config)

        for _, (territory, happiness, _) in world.get_components(
            (Territory, PopulationHappiness, Active)
        ):
            # Ignore territories with happiness over the threshold
            if happiness.value > config.happiness_revolt_threshold:
                continue

            # Ignore territories that are already revolting
            if territory.gameobject.has_component(InRevolt):
                continue

            # Ignore territories that are not controlled by a family
            if territory.controlling_family is None:
                continue

            territory.gameobject.add_component(InRevolt(start_date=current_date))

            RevoltEvent(
                subject=territory.controlling_family,
                territory=territory.gameobject,
            ).log_event()


class RevoltUpdateSystem(System):
    """Updates existing revolts."""

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate)
        config = world.resources.get_resource(Config)

        for _, (territory, happiness, in_revolt, _) in world.get_components(
            (Territory, PopulationHappiness, InRevolt, Active)
        ):
            elapsed_months = (current_date - in_revolt.start_date).total_months

            # Ignore territories that have not reached the point of no return
            if elapsed_months < config.months_to_quell_revolt:
                continue

            if territory.controlling_family is None:
                territory.gameobject.remove_component(InRevolt)
                happiness.base_value = config.base_territory_happiness
                continue

            controlling_family_component = territory.controlling_family.get_component(
                Family
            )
            if family_head := controlling_family_component.head:
                character_component = family_head.get_component(Character)
                character_component.influence_points -= 500

            territory.gameobject.remove_component(InRevolt)
            happiness.base_value = config.base_territory_happiness

            if controlling_family_component.head:
                LostTerritoryEvent(
                    subject=controlling_family_component.head,
                    territory=territory.gameobject,
                ).log_event()

            RemovedFromPowerEvent(
                subject=territory.controlling_family,
                territory=territory.gameobject,
            ).log_event()

            territory.controlling_family.get_component(FamilyPrestige).base_value -= 20

            # Remove the current family from power
            set_territory_controlling_family(territory.gameobject, None)


class TerritoryRandomEventSystem(System):
    """Random events can happen to territories to change their happiness.

    Outside of the actions of the controlling family, territories can be subject
    to various random events that affect their happiness state. We select from them
    each month like a deck of cards.

    """

    __system_group__ = "UpdateSystems"

    _random_events: ClassVar[dict[str, tuple[float, Callable[[GameObject], None]]]] = {}

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)

        for _, (territory, _) in world.get_components((Territory, Active)):
            if territory.controlling_family is None:
                continue

            event_name = self.choose_random_event(rng)

            if event_name is None:
                continue

            event_fn = self._random_events[event_name][1]

            event_fn(territory.gameobject)

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


@TerritoryRandomEventSystem.random_event("nothing", 10)
def nothing_event(_: GameObject) -> None:
    """Do Nothing."""
    return


@TerritoryRandomEventSystem.random_event("poor harvest", 0.5)
def poor_harvest_event(territory: GameObject) -> None:
    """Poor harvest."""
    current_date = territory.world.resources.get_resource(SimDate)
    happiness_component = territory.get_component(PopulationHappiness)

    happiness_component.base_value -= 10

    _logger.info(
        "[%s]: %s has suffered a poor harvest.",
        current_date.to_iso_str(),
        territory.name_with_uid,
    )


@TerritoryRandomEventSystem.random_event("disease", 0.5)
def disease_event(territory: GameObject) -> None:
    """Do Nothing."""
    current_date = territory.world.resources.get_resource(SimDate)
    happiness_component = territory.get_component(PopulationHappiness)

    happiness_component.base_value -= 10

    _logger.info(
        "[%s]: %s has suffered a disease outbreak.",
        current_date.to_iso_str(),
        territory.name_with_uid,
    )


@TerritoryRandomEventSystem.random_event("bountiful harvest", 0.5)
def bountiful_harvest_event(territory: GameObject) -> None:
    """Do Nothing."""
    current_date = territory.world.resources.get_resource(SimDate)
    happiness_component = territory.get_component(PopulationHappiness)

    happiness_component.base_value += 10

    _logger.info(
        "[%s]: %s had a bountiful harvest.",
        current_date.to_iso_str(),
        territory.name_with_uid,
    )


class InfluencePointGainSystem(System):
    """Increases the influence points for characters."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        config = world.resources.get_resource(Config)

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
                config.influence_points_max,
            )

            character.influence_points = max(0, character.influence_points)

            _logger.debug(
                "[%s]: %s has %d influence points",
                world.resources.get_resource(SimDate).to_iso_str(),
                character.gameobject.name_with_uid,
                character.influence_points,
            )


class TerritoryInfluencePointBoostSystem(System):
    """The head of a family that controls a territory gets a influence point increase."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (territory, _) in world.get_components((Territory, Active)):
            if territory.controlling_family is None:
                continue

            family_component = territory.controlling_family.get_component(Family)

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

            if (
                character.life_stage < LifeStage.YOUNG_ADULT
                or character.life_stage == LifeStage.SENIOR
            ):
                continue

            if not rng.random() < chance_get_married:
                continue

            eligible_singles: list[Character] = []

            if (
                character.sexual_orientation == SexualOrientation.HETEROSEXUAL
                and character.sex == Sex.MALE
            ):
                # Looking for heterosexual, bisexual, or asexual women
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
                        or c.sexual_orientation == SexualOrientation.ASEXUAL
                    )
                    and c.gameobject not in character.siblings
                    and c.gameobject != character.mother
                    and c.gameobject != character.father
                    and c.gameobject != character.biological_father
                    and c.gameobject not in character.children
                    and c.gameobject not in character.grandchildren
                    and c.gameobject not in character.grandparents
                    and len(c.grandparents.intersection(character.grandparents)) < 2
                    and c != character
                ]

            if (
                character.sexual_orientation == SexualOrientation.HETEROSEXUAL
                and character.sex == Sex.FEMALE
            ):
                # Looking for heterosexual, bisexual, or asexual men
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
                        or c.sexual_orientation == SexualOrientation.ASEXUAL
                    )
                    and c.gameobject not in character.siblings
                    and c.gameobject != character.mother
                    and c.gameobject != character.father
                    and c.gameobject != character.biological_father
                    and c.gameobject not in character.children
                    and c.gameobject not in character.grandchildren
                    and c.gameobject not in character.grandparents
                    and len(c.grandparents.intersection(character.grandparents)) < 2
                    and c != character
                ]

            if (
                character.sexual_orientation == SexualOrientation.HOMOSEXUAL
                and character.sex == Sex.MALE
            ):
                # Looking for homosexual, asexual, or bisexual men
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
                        or c.sexual_orientation == SexualOrientation.ASEXUAL
                    )
                    and c.gameobject not in character.siblings
                    and c.gameobject != character.mother
                    and c.gameobject != character.father
                    and c.gameobject != character.biological_father
                    and c.gameobject not in character.children
                    and c.gameobject not in character.grandchildren
                    and c.gameobject not in character.grandparents
                    and len(c.grandparents.intersection(character.grandparents)) < 2
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
                        or c.sexual_orientation == SexualOrientation.ASEXUAL
                    )
                    and c.gameobject not in character.siblings
                    and c.gameobject != character.mother
                    and c.gameobject != character.father
                    and c.gameobject != character.biological_father
                    and c.gameobject not in character.children
                    and c.gameobject not in character.grandchildren
                    and c.gameobject not in character.grandparents
                    and len(c.grandparents.intersection(character.grandparents)) < 2
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

            if (
                character.sexual_orientation == SexualOrientation.ASEXUAL
                and character.sex == Sex.FEMALE
            ):
                # Looking for anyone asexual
                eligible_singles = [
                    c
                    for _, (c, _) in world.get_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and (
                        c.sexual_orientation == SexualOrientation.ASEXUAL
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

                # new spouse loses all their heirs
                if new_spouse.heir is not None:
                    remove_heir(new_spouse.gameobject)

            # Case 2: The character is head of their family and their spouse is not
            if character.gameobject.has_component(
                HeadOfFamily
            ) and not new_spouse.gameobject.has_component(HeadOfFamily):
                family_a = character.family
                assert family_a is not None
                set_character_family(new_spouse.gameobject, family_a)

                # new spouse loses heir eligibility
                if new_spouse.heir_to is not None:
                    remove_heir(new_spouse.heir_to)

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

                # character loses heir eligibility
                if new_spouse.heir_to is not None:
                    remove_heir(new_spouse.heir_to)

            # Case 4: Neither character is head of their family.
            if not character.gameobject.has_component(
                HeadOfFamily
            ) and not new_spouse.gameobject.has_component(HeadOfFamily):
                family_a = character.family
                assert family_a is not None
                set_character_family(new_spouse.gameobject, family_a)

                # new spouse loses heir eligibility
                if new_spouse.heir_to is not None:
                    remove_heir(new_spouse.heir_to)

            MarriageEvent(character.gameobject, new_spouse.gameobject).log_event()
            MarriageEvent(new_spouse.gameobject, character.gameobject).log_event()


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

            if not (character.sex == Sex.FEMALE and spouse.sex == Sex.MALE):
                continue

            if character.gameobject.has_component(Pregnancy):
                continue

            character_fertility_comp = marriage.character.get_component(Fertility)
            character_fertility = character_fertility_comp.normalized

            spouse_fertility_comp = marriage.spouse.get_component(Fertility)
            spouse_fertility = spouse_fertility_comp.normalized

            if character_fertility <= 0 or spouse_fertility <= 0:
                continue

            chance_have_child = (character_fertility + spouse_fertility) / 2

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

            character_fertility_comp.base_value -= 25

            PregnancyEvent(character.gameobject).log_event()


class ChildBirthSystem(System):
    """Spawns new children when pregnant characters reach their due dates."""

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate)

        baby_factory = world.resources.get_resource(PCGFactories).baby_factory

        for _, (character, pregnancy, fertility, _) in world.get_components(
            (Character, Pregnancy, Fertility, Active)
        ):
            if pregnancy.due_date > current_date:
                continue

            father = pregnancy.actual_father

            baby = baby_factory.generate_child(
                mother=character.gameobject,
                father=father,
            )

            set_character_mother(baby, character.gameobject)
            set_character_father(baby, pregnancy.assumed_father)
            set_character_biological_father(baby, pregnancy.actual_father)

            # Set grandparent/child relationships
            update_grandparent_relations(baby, [character.mother, character.father])

            if pregnancy.assumed_father is not None:
                assumed_father_character_comp = pregnancy.assumed_father.get_component(
                    Character
                )
                update_grandparent_relations(
                    baby,
                    [
                        assumed_father_character_comp.mother,
                        assumed_father_character_comp.father,
                    ],
                )

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
            father_children = father.get_component(Character).children
            for existing_child in father_children:
                if existing_child == baby:
                    continue

                set_relation_sibling(baby, existing_child)
                set_relation_sibling(existing_child, baby)

            character.gameobject.remove_component(Pregnancy)

            # Reduce the character's fertility according to their species
            fertility.base_value -= character.species.fertility_cost_per_child

            ChildBirthEvent(subject=character.gameobject, child=baby).log_event()

            BirthEvent(subject=baby).log_event()


class ActionCooldownSystem(System):
    """Update all active schemes."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (brain, _) in world.get_components((AIBrain, Active)):
            for key in brain.action_cooldowns:
                brain.action_cooldowns[key] -= 1


class SchemeUpdateSystems(SystemGroup):
    """Groups all the scheme updaters."""

    __system_group__ = "EarlyUpdateSystems"


class AllianceSchemeUpdateSystem(System):
    """Updates all alliance schemes."""

    __system_group__ = "SchemeUpdateSystems"

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate).copy()

        for _, (scheme, _, _) in world.get_components((Scheme, AllianceScheme, Active)):
            if scheme.is_valid is False:
                destroy_alliance_scheme(scheme.gameobject)
                continue

            elapsed_months = (current_date - scheme.start_date).total_months

            if elapsed_months >= scheme.required_time:
                # Check that other people have joined the scheme for the alliance to be
                # created. Otherwise, this scheme fails
                if len(scheme.members) > 1:

                    # Need to get all the families of scheme members
                    alliance_families: list[GameObject] = []
                    for member in scheme.members:
                        character_component = member.get_component(Character)
                        if character_component.family is None:
                            raise RuntimeError("Alliance member is missing family.")
                        alliance_families.append(character_component.family)

                    alliance = start_alliance(*alliance_families)

                    # Increase the opinion between alliance members.
                    for member_a in scheme.members:
                        for member_b in scheme.members:
                            if member_a == member_b:
                                continue

                            get_relationship(member_a, member_b).get_component(
                                Opinion
                            ).base_value += 20
                            get_relationship(member_b, member_a).get_component(
                                Opinion
                            ).base_value += 20

                    get_family_of(scheme.initiator).get_component(
                        FamilyPrestige
                    ).base_value += 30

                    scheme.initiator.get_component(
                        CharacterMetrics
                    ).data.num_alliances_founded += 1

                    AllianceFoundedEvent(
                        subject=scheme.initiator,
                        alliance=alliance,
                    ).log_event()

                else:
                    scheme.initiator.get_component(
                        CharacterMetrics
                    ).data.num_failed_alliance_attempts += 1

                    AllianceSchemeFailedEvent(scheme.initiator).log_event()

                scheme.is_valid = False
                destroy_alliance_scheme(scheme.gameobject)


class WarSchemeUpdateSystem(System):
    """Updates all active war schemes."""

    __system_group__ = "SchemeUpdateSystems"

    @staticmethod
    def are_in_same_alliance(character_a: GameObject, character_b: GameObject) -> bool:
        """Check if two characters belong to the same alliance."""
        character_a_family = character_a.get_component(Character).family

        if character_a_family is None:
            return False

        character_a_alliance = character_a_family.get_component(Family).alliance

        character_b_family = character_b.get_component(Character).family

        if character_b_family is None:
            return False

        character_b_alliance = character_a_family.get_component(Family).alliance

        return (
            character_a_alliance is not None
            and character_b_alliance is not None
            and character_a_alliance == character_b_alliance
        )

    @staticmethod
    def get_family(character: GameObject) -> GameObject:
        """Get the reference to a character's family."""
        character_family = character.get_component(Character).family
        if character_family is None:
            raise RuntimeError(f"{character.name_with_uid} does not have a family.")
        return character_family

    @staticmethod
    def get_alliance(family: GameObject) -> GameObject:
        """Get  reference to a family's alliance."""
        family_alliance = family.get_component(Family).alliance
        if family_alliance is None:
            raise RuntimeError(f"{family.name_with_uid} does not have an alliance.")
        return family_alliance

    @staticmethod
    def add_alliance_members_as_allies(
        war: GameObject, character: GameObject, role: WarRole
    ) -> None:
        """Add a character's alliance members as allies in a war."""
        character_family = WarSchemeUpdateSystem.get_family(character)
        character_alliance = character_family.get_component(Family).alliance

        if character_alliance is not None:
            alliance_component = character_alliance.get_component(Alliance)
            for member_family in alliance_component.member_families:
                if member_family == character_family:
                    continue

                member_family_head = member_family.get_component(Family).head
                if member_family_head is not None:
                    # raise RuntimeError(
                    #     f"{member_family.name_with_uid} is missing a head."
                    # )

                    join_war_as(war, member_family, role)

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate).copy()

        for _, (scheme, war_scheme, _) in world.get_components(
            (Scheme, WarScheme, Active)
        ):
            # Cancel the scheme if has been invalidated by an external system
            if scheme.is_valid is False:
                destroy_war_scheme(scheme.gameobject)
                continue

            # Cancel the scheme if the initiator and scheme target belong to the
            # same alliance
            if self.are_in_same_alliance(scheme.initiator, war_scheme.defender):
                scheme.is_valid = False
                destroy_war_scheme(scheme.gameobject)
                continue

            elapsed_months = (current_date - scheme.start_date).total_months

            if elapsed_months >= scheme.required_time:
                aggressor_family = self.get_family(scheme.initiator)
                defender_family = self.get_family(war_scheme.defender)

                scheme.initiator.get_component(CharacterMetrics).data.num_wars += 1
                war_scheme.defender.get_component(CharacterMetrics).data.num_wars += 1
                scheme.initiator.get_component(
                    CharacterMetrics
                ).data.num_wars_started += 1
                scheme.initiator.get_component(
                    CharacterMetrics
                ).data.date_of_last_declared_war = current_date.copy()

                war = start_war(aggressor_family, defender_family, war_scheme.territory)

                self.add_alliance_members_as_allies(
                    war, scheme.initiator, WarRole.AGGRESSOR_ALLY
                )

                self.add_alliance_members_as_allies(
                    war, war_scheme.defender, WarRole.DEFENDER_ALLY
                )

                DeclareWarEvent(
                    subject=scheme.initiator,
                    target=war_scheme.defender,
                    territory=war_scheme.territory,
                ).log_event()

                DefendingTerritoryEvent(
                    subject=war_scheme.defender,
                    opponent=scheme.initiator,
                    territory=war_scheme.territory,
                ).log_event()

                scheme.is_valid = False
                destroy_war_scheme(scheme.gameobject)


class CoupSchemeUpdateSystem(System):
    """Updates all active war schemes."""

    __system_group__ = "SchemeUpdateSystems"

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate).copy()
        rng = world.resources.get_resource(random.Random)

        for _, (scheme, coup_scheme, _) in world.get_components(
            (Scheme, CoupScheme, Active)
        ):
            if scheme.is_valid is False:
                destroy_coup_scheme(scheme.gameobject)
                continue

            if not coup_scheme.target.is_active:
                destroy_coup_scheme(scheme.gameobject)
                continue

            elapsed_months = (current_date - scheme.start_date).total_months

            if elapsed_months >= scheme.required_time:
                # Check that other people have joined the scheme for the alliance to be
                # created. Otherwise, this scheme fails
                if len(scheme.members) > 2:

                    # Kill the current ruler.
                    current_ruler = get_current_ruler(world)

                    if current_ruler is None:
                        scheme.is_valid = False
                        continue

                    RuleOverthrownEvent(
                        subject=current_ruler, usurper=scheme.initiator
                    ).log_event()

                    UsurpEvent(
                        subject=scheme.initiator, former_ruler=current_ruler
                    ).log_event()

                    ruler_family = current_ruler.get_component(Character).family

                    current_ruler.get_component(Character).killed_by = scheme.initiator

                    DieAction(
                        current_ruler, pass_crown=False, cause_of_death="assassination"
                    ).execute()

                    if ruler_family is not None:
                        # Remove the rulers family from being in control of their home
                        # base
                        family_component = ruler_family.get_component(Family)

                        for territory in family_component.territories:
                            territory_component = territory.get_component(Territory)
                            if territory_component.controlling_family == ruler_family:
                                set_territory_controlling_family(territory, None)

                    # They are discovered and put to death
                    for member in scheme.members:
                        member_character_comp = member.get_component(Character)

                        # Reduce traitor family prestige
                        assert member_character_comp.family

                        member_character_comp.family.get_component(
                            FamilyPrestige
                        ).base_value += 50

                        if member != scheme.initiator:
                            get_relationship(scheme.initiator, member).get_component(
                                Opinion
                            ).base_value += 30

                    set_current_ruler(world, scheme.initiator)

                scheme.is_valid = False
                destroy_coup_scheme(scheme.gameobject)

            else:
                # Check if the coup is discovered by the royal family
                intrigue_score = scheme.initiator.get_component(Intrigue).normalized

                # Nothing happens
                if (rng.random() * 0.75) < intrigue_score:
                    continue

                CoupSchemeDiscoveredEvent(scheme.initiator).log_event()

                # They are discovered and put to death
                for member in scheme.members:
                    member_character_comp = member.get_component(Character)

                    # Reduce traitor family prestige
                    assert member_character_comp.family

                    member_character_comp.family.get_component(
                        FamilyPrestige
                    ).base_value -= 50

                    # Execute traitor
                    member_character_comp.killed_by = coup_scheme.target
                    SentencedToDeathEvent(member, "treason").log_event()
                    DieAction(member, "treason").execute()

                scheme.is_valid = False
                destroy_coup_scheme(scheme.gameobject)


class WarUpdateSystem(System):
    """Updates all active wars."""

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)

        for _, (war, _) in world.get_components((War, Active)):

            # Check that the family heads are alive
            aggressor_family_head = war.aggressor.get_component(Family).head
            defender_family_head = war.defender.get_component(Family).head

            if aggressor_family_head is None or defender_family_head is None:
                war.gameobject.deactivate()
                end_war(war.gameobject, None)
                continue

            prowess_mean, prowess_stdev = calculate_warrior_prowess_dist(war)
            aggressor_score = calculate_war_score(
                war.aggressor, list(war.aggressor_allies)
            )
            defender_score = calculate_war_score(
                war.defender, list(war.defender_allies)
            )
            base_aggressor_win_probability = calculate_aggressor_win_probability(
                aggressor_score, defender_score
            )
            aggressor_win_probability = base_aggressor_win_probability

            assert aggressor_family_head
            assert defender_family_head

            # Adjust win probability based on aggressor luck
            aggressor_luck_level = get_luck_level(aggressor_family_head)
            if aggressor_luck_level == StatLevel.TERRIBLE:
                aggressor_win_probability -= 0.1
            elif aggressor_luck_level == StatLevel.EXCELLENT:
                aggressor_win_probability += 0.1

            # Adjust win probability based on defender luck
            defender_luck_level = get_luck_level(defender_family_head)
            if defender_luck_level == StatLevel.TERRIBLE:
                aggressor_win_probability += 0.1
            elif defender_luck_level == StatLevel.EXCELLENT:
                aggressor_win_probability -= 0.1

            # Random roll to see who wins
            if rng.random() < aggressor_win_probability:
                winner = war.aggressor
                winner_allies = war.aggressor_allies
                loser = war.defender
                loser_allies = war.defender_allies
            else:
                winner = war.defender
                winner_allies = war.defender_allies
                loser = war.aggressor
                loser_allies = war.aggressor_allies

            # Determine casualties
            casualties: list[GameObject] = []

            for warrior in winner.get_component(Family).warriors:
                casualty_chance = get_casualty_chance(
                    prowess_mean,
                    prowess_stdev,
                    warrior.get_component(Prowess).value,
                )

                # Adjust Casualty Chance based on luck
                warrior_luck_level = get_luck_level(warrior)
                if warrior_luck_level == StatLevel.TERRIBLE:
                    casualty_chance += 0.1
                elif warrior_luck_level == StatLevel.EXCELLENT:
                    casualty_chance -= 0.1

                # Roll for casualty
                if random.random() < casualty_chance:
                    casualties.append(warrior)

            for family in winner_allies:
                for warrior in family.get_component(Family).warriors:
                    casualty_chance = get_casualty_chance(
                        prowess_mean,
                        prowess_stdev,
                        warrior.get_component(Prowess).value,
                    )

                    # Adjust Casualty Chance based on luck
                    warrior_luck_level = get_luck_level(warrior)
                    if warrior_luck_level == StatLevel.TERRIBLE:
                        casualty_chance += 0.1
                    elif warrior_luck_level == StatLevel.EXCELLENT:
                        casualty_chance -= 0.1

                    # Roll for casualty
                    if random.random() < casualty_chance:
                        casualties.append(warrior)

            for warrior in loser.get_component(Family).warriors:
                casualty_chance = get_casualty_chance(
                    prowess_mean, prowess_stdev, warrior.get_component(Prowess).value
                )

                # Adjust because they lost
                casualty_chance += 0.15

                # Adjust Casualty Chance based on luck
                warrior_luck_level = get_luck_level(warrior)
                if warrior_luck_level == StatLevel.TERRIBLE:
                    casualty_chance += 0.1
                elif warrior_luck_level == StatLevel.EXCELLENT:
                    casualty_chance -= 0.1

                # Roll for casualty
                if random.random() < casualty_chance:
                    casualties.append(warrior)

            for family in loser_allies:
                for warrior in family.get_component(Family).warriors:
                    casualty_chance = get_casualty_chance(
                        prowess_mean,
                        prowess_stdev,
                        warrior.get_component(Prowess).value,
                    )

                    # Adjust because they lost
                    casualty_chance += 0.15

                    # Adjust Casualty Chance based on luck
                    warrior_luck_level = get_luck_level(warrior)
                    if warrior_luck_level == StatLevel.TERRIBLE:
                        casualty_chance += 0.1
                    elif warrior_luck_level == StatLevel.EXCELLENT:
                        casualty_chance -= 0.1

                    # Roll for casualty
                    if random.random() < casualty_chance:
                        casualties.append(warrior)

            if winner == war.aggressor:
                # Aggressor wins the battle

                # Remove the defender from controlling the territory and instate the
                set_territory_controlling_family(war.contested_territory, war.aggressor)

                # TODO: Fire and log events for winning and losing wars
                _logger.info(
                    "[%s]: the %s family defeated the %s family and has taken control "
                    "of the %s territory.",
                    world.resources.get_resource(SimDate).to_iso_str(),
                    war.aggressor.name_with_uid,
                    war.defender.name_with_uid,
                    war.contested_territory.name_with_uid,
                )

                aggressor_family_head = war.aggressor.get_component(Family).head
                if aggressor_family_head:
                    aggressor_family_head.get_component(
                        CharacterMetrics
                    ).data.num_wars_won += 1

                    aggressor_family_head.get_component(
                        CharacterMetrics
                    ).data.num_territories_taken += 1

                defending_family_head = war.defender.get_component(Family).head
                if defending_family_head:
                    defending_family_head.get_component(
                        CharacterMetrics
                    ).data.num_wars_lost += 1

                war.aggressor.get_component(FamilyPrestige).base_value += 40
                war.defender.get_component(FamilyPrestige).base_value -= 20

                end_war(war.gameobject, war.aggressor)

            else:
                # Defender wins the battle
                # Aggressor loses influence points

                # TODO: Fire and log events for winning and losing wars
                _logger.info(
                    "[%s]: the %s family failed to defeat the %s family over control "
                    "of the %s territory.",
                    world.resources.get_resource(SimDate).to_iso_str(),
                    war.aggressor.name_with_uid,
                    war.defender.name_with_uid,
                    war.contested_territory.name_with_uid,
                )

                aggressor_family_head = war.aggressor.get_component(Family).head
                if aggressor_family_head:
                    aggressor_family_head.get_component(
                        CharacterMetrics
                    ).data.num_wars_lost += 1

                defending_family_head = war.defender.get_component(Family).head
                if defending_family_head:
                    defending_family_head.get_component(
                        CharacterMetrics
                    ).data.num_wars_won += 1

                war.aggressor.get_component(FamilyPrestige).base_value -= 50
                war.defender.get_component(FamilyPrestige).base_value += 35

                end_war(war.gameobject, war.defender)

            # Kill off the casualties
            for character in casualties:
                DieAction(character, cause_of_death="war").execute()


class FamilyRefillSystem(System):
    """Spawns new families in territories that have too few families."""

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate)
        for _, (territory, _) in world.get_components((Territory, Active)):
            if len(territory.families) < 3:
                family = generate_family(world)
                family_component = family.get_component(Family)
                set_family_home_base(family, territory.gameobject)
                family_component.territories.add(territory.gameobject)
                _logger.info(
                    "[%s] The %s family has risen to prominence in the %s territory.",
                    current_date.to_iso_str(),
                    family_component.name,
                    territory.name,
                )


class HeirDeclarationSystem(System):
    """Family heads missing an heir will try to name an heir."""

    __system_group__ = "UpdateSystems"

    @staticmethod
    def get_oldest_child(character: Character) -> Optional[GameObject]:
        """Get the oldest living child of the character who is in the same family."""

        child_list: list[tuple[GameObject, float]] = []

        for child in character.children:
            child_character_component = child.get_component(Character)

            if not child.has_component(Active):
                continue

            if child_character_component.family == character.family:
                child_list.append((child, child_character_component.age))

            child_list.sort(key=lambda e: e[1])

            if child_list:
                return child_list[-1][0]

            return None

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate)

        for _, (character, _, _) in world.get_components(
            (Character, HeadOfFamily, Active)
        ):
            if character.heir is not None:
                continue

            oldest_child = HeirDeclarationSystem.get_oldest_child(character)

            if oldest_child:
                oldest_child_character_comp = oldest_child.get_component(Character)
                set_heir(character.gameobject, oldest_child)
                oldest_child_character_comp.heir_to = character.gameobject
                _logger.info(
                    "[%s]: %s declared %s their heir.",
                    current_date.to_iso_str(),
                    character.gameobject.name_with_uid,
                    oldest_child,
                )


class OrphanIdentificationSystem(System):
    """Identifies orphans in a family."""

    def on_update(self, world: World) -> None:
        current_date = world.resources.get_resource(SimDate)

        for _, (character, _) in world.get_components((Character, Active)):
            mother = character.mother
            father = character.father

            missing_mother = mother is None or not mother.has_component(Active)
            missing_father = father is None or not father.has_component(Active)
            is_not_adult = character.life_stage <= LifeStage.ADOLESCENT

            if missing_father and missing_mother and is_not_adult:
                _logger.info(
                    "[%s]: %s is an orphan.",
                    current_date.to_iso_str(),
                    character.gameobject.name_with_uid,
                )


class OrphanAdoptionSystem(System):
    """Identify family heads without children."""

    @staticmethod
    def is_orphan(character: Character) -> bool:
        """Check if a character is an orphan."""
        mother = character.mother
        father = character.father

        missing_mother = mother is None or not mother.has_component(Active)
        missing_father = father is None or not father.has_component(Active)
        is_not_adult = character.life_stage <= LifeStage.ADOLESCENT

        return missing_father and missing_mother and is_not_adult

    @staticmethod
    def get_orphans_in_family(character_component: Character) -> list[GameObject]:
        """Get all orphans in the family."""

        family = character_component.family
        if family is None:
            return []

        orphans: list[GameObject] = []
        family_component = family.get_component(Family)
        for member in family_component.active_members:
            member_character = member.get_component(Character)
            if OrphanAdoptionSystem.is_orphan(member_character):
                orphans.append(member)

        return orphans

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)
        current_date = world.resources.get_resource(SimDate)

        for _, (character, _, _) in world.get_components(
            (Character, HeadOfFamily, Active)
        ):
            if character.life_stage < LifeStage.ADULT:
                continue

            if character.heir is not None:
                continue

            # Adopt orphan
            orphans = OrphanAdoptionSystem.get_orphans_in_family(character)

            if orphans:

                chosen_orphan = rng.choice(orphans)
                character.children.add(chosen_orphan)
                _logger.info(
                    "[%s]: %s adopted %s.",
                    current_date.to_iso_str(),
                    character.gameobject.name_with_uid,
                    chosen_orphan.name_with_uid,
                )


class CheatSchemeUpdateSystem(System):
    """Updates active cheating schemes."""

    __system_group__ = "SchemeUpdateSystems"

    def on_update(self, world: World) -> None:
        rng = world.resources.get_resource(random.Random)

        for _, (scheme, cheating_scheme) in world.get_components(
            (Scheme, CheatingScheme)
        ):
            # Destroy invalid schemes
            if scheme.is_valid is False:
                destroy_scheme(scheme.gameobject)
                continue

            # Destroy the scheme if the accomplice is no longer active
            if not cheating_scheme.accomplice.is_active:
                destroy_scheme(scheme.gameobject)
                continue

            # Destroy the scheme if the initiator is no longer active
            if not scheme.initiator.is_active:
                destroy_scheme(scheme.gameobject)
                continue

            # Destroy the scheme if the initiator is no longer married
            initiator_character = scheme.initiator.get_component(Character)
            if initiator_character.spouse is None:
                destroy_scheme(scheme.gameobject)
                continue

            # Evaluate the accomplices willingness to participate in
            # this activity if they are married
            accomplice_character = cheating_scheme.accomplice.get_component(Character)
            if accomplice_character.spouse is not None:
                accomplice_cheating_action = CheatOnSpouseAction(
                    cheating_scheme.accomplice, scheme.initiator
                )

                action_utility = accomplice_cheating_action.calculate_utility()

                if rng.random() < action_utility:
                    # Have to create an instance of the cheating action for the
                    # initiator
                    CheatOnSpouseAction(
                        scheme.initiator, cheating_scheme.accomplice
                    ).execute()

                    accomplice_cheating_action.execute()

                else:
                    # Invalidate the scheme because the accomplice is not willing to
                    # cheat
                    scheme.is_valid = False

                    # Lower the attraction between the characters
                    get_relationship(
                        scheme.initiator, cheating_scheme.accomplice
                    ).get_component(Attraction).base_value -= 10

                    get_relationship(
                        cheating_scheme.accomplice, scheme.initiator
                    ).get_component(Attraction).base_value -= 10

                    get_relationship(
                        cheating_scheme.accomplice, scheme.initiator
                    ).get_component(Opinion).base_value -= 15

            # The accomplice is not married and so this is only sex
            else:
                accomplice_sex_action = SexAction(
                    cheating_scheme.accomplice, scheme.initiator
                )

                action_utility = accomplice_sex_action.calculate_utility()

                if rng.random() < action_utility:
                    # Have to create an instance of the cheating action for the
                    # initiator
                    CheatOnSpouseAction(
                        scheme.initiator, cheating_scheme.accomplice
                    ).execute()

                    accomplice_sex_action.execute()

                else:
                    # Invalidate the scheme because the accomplice is not willing to
                    # have sex
                    scheme.is_valid = False

                    # Lower the attraction between the characters
                    get_relationship(
                        scheme.initiator, cheating_scheme.accomplice
                    ).get_component(Attraction).base_value -= 10

                    get_relationship(
                        cheating_scheme.accomplice, scheme.initiator
                    ).get_component(Attraction).base_value -= 10

                    get_relationship(
                        cheating_scheme.accomplice, scheme.initiator
                    ).get_component(Opinion).base_value -= 15

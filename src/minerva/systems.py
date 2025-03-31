# pylint: disable=C0302
"""Minerva Base Systems."""

import logging
import random
from typing import Callable, ClassVar, Optional

from ordered_set import OrderedSet

from minerva.actions.actions import (
    BecomeAdolescentAction,
    BecomeAdultAction,
    BecomeChildAction,
    BecomeFamilyHead,
    BecomeSeniorAction,
    BecomeYoungAdultAction,
    ClaimThroneAction,
    CreateAllianceAction,
    DeclareWar,
    DieAction,
    DiscoverCoupScheme,
    GetMarriedAction,
    GiveBirth,
    GoIntoRevolt,
    LoseControlOfTerritory,
    OverthrowRulerAction,
    SentenceToDeath,
)
from minerva.actions.base_types import (
    AIAction,
    AIBehaviorLibrary,
    CharacterController,
    Scheme,
    score_actions,
)
from minerva.actions.scheme_types import AllianceScheme, CoupScheme, WarScheme
from minerva.characters.components import (
    Character,
    Diplomacy,
    Dynasty,
    DynastyTracker,
    Family,
    FamilyRoleFlags,
    Fertility,
    HeadOfFamily,
    LifeStage,
    Marriage,
    Pregnancy,
    Prestige,
    Prowess,
    Ruler,
    Sex,
    SexualOrientation,
)
from minerva.characters.helpers import (
    RemoveCharacterFromPlay,
    RemoveFamilyFromPlay,
    assign_family_member_to_roles,
    get_advisor_candidates,
    get_family_of,
    get_fertility,
    get_intrigue_skill,
    get_lifespan,
    get_warrior_candidates,
    increment_prestige_base,
    set_character_age,
    set_character_life_stage,
    set_family_head,
    set_family_home_base,
    set_fertility_base,
    set_heir,
)
from minerva.characters.metric_data import CharacterMetrics
from minerva.characters.stat_helpers import StatLevel, get_luck_level
from minerva.characters.succession_helpers import (
    end_current_dynasty,
    get_current_ruler,
    get_succession_depth_chart,
    remove_current_ruler,
    set_current_ruler,
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
from minerva.ecs import Active, Entity, System, SystemGroup, World
from minerva.game_action import ActionSystem
from minerva.game_state import GameState
from minerva.pcg.character import FamilyGenOptions, spawn_family
from minerva.pcg.world_map import GenerateMap, generate_world_map
from minerva.relationships.base_types import Opinion
from minerva.relationships.helpers import get_relationship
from minerva.world_map.components import InRevolt, PopulationHappiness, Territory
from minerva.world_map.helpers import set_territory_controlling_family

_logger = logging.getLogger(__name__)


class TimeSystem(System):
    """Increments the current date/time."""

    __system_group__ = "LateUpdateSystems"
    __update_order__ = ("last",)

    def on_update(self, world: World) -> None:
        world.get_resource(GameState).year += 1


class CharacterAgingSystem(System):
    """Age characters over time."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for uid, (character_comp, fertility, _) in world.query_components(
            (Character, Fertility, Active)
        ):
            character = world.get_entity(uid)

            age = character_comp.age + 1
            set_character_age(character, age)

            species = character_comp.species

            if species.can_physically_age:
                if age >= species.senior_age:
                    if character_comp.life_stage != LifeStage.SENIOR:
                        fertility_max = (
                            species.senior_male_fertility
                            if character_comp.sex == Sex.MALE
                            else species.senior_female_fertility
                        )

                        set_fertility_base(
                            character, min(fertility.base_value, fertility_max)
                        )

                        BecomeSeniorAction(character).execute()

                elif age >= species.adult_age:
                    if character_comp.life_stage != LifeStage.ADULT:
                        fertility_max = (
                            species.adult_male_fertility
                            if character_comp.sex == Sex.MALE
                            else species.adult_female_fertility
                        )

                        set_fertility_base(
                            character, min(fertility.base_value, fertility_max)
                        )

                        set_character_life_stage(character_comp.entity, LifeStage.ADULT)

                        BecomeAdultAction(character).execute()

                elif age >= species.young_adult_age:
                    if character_comp.life_stage != LifeStage.YOUNG_ADULT:
                        fertility_max = (
                            species.young_adult_male_fertility
                            if character_comp.sex == Sex.MALE
                            else species.young_adult_female_fertility
                        )

                        set_fertility_base(
                            character, min(fertility.base_value, fertility_max)
                        )

                        BecomeYoungAdultAction(character).execute()

                elif age >= species.adolescent_age:
                    if character_comp.life_stage != LifeStage.ADOLESCENT:
                        fertility_max = (
                            species.adolescent_male_fertility
                            if character_comp.sex == Sex.MALE
                            else species.adolescent_female_fertility
                        )

                        set_fertility_base(
                            character, min(fertility.base_value, fertility_max)
                        )

                        BecomeAdolescentAction(character).execute()

                else:
                    if character_comp.life_stage != LifeStage.CHILD:
                        BecomeChildAction(character).execute()


class CharacterLifespanSystem(System):
    """Kills of characters who have reached their lifespan."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for uid, (character_comp, _) in world.query_components((Character, Active)):
            character = world.get_entity(uid)
            lifespan = get_lifespan(character)
            if character_comp.age >= lifespan:
                DieAction(character, cause="old age").execute()


class FamilyHeadSuccessionSystem(System):
    """Appoints new family heads to families without one.

    This system will remove families from play that are unable to find a successor.
    """

    __system_group__ = "LateUpdateSystems"

    def on_start(self, world: World) -> None:
        world.get_resource(ActionSystem).add_listener(
            RemoveCharacterFromPlay, self.handle_succession, "pre"
        )
        world.get_resource(ActionSystem).add_listener(
            RemoveCharacterFromPlay, self.handle_succession_fail, "post"
        )

    @staticmethod
    def handle_succession(action: RemoveCharacterFromPlay) -> None:
        """Handle a character death."""
        if action.character.has_component(HeadOfFamily):
            family = action.character.get_component(HeadOfFamily).family

            set_family_head(family, None)

            if FamilyHeadSuccessionSystem.try_pass_power_to_heir(
                action.character, family
            ):
                return

            FamilyHeadSuccessionSystem.try_pass_power_to_descendent(
                action.character, family
            )

    @staticmethod
    def handle_succession_fail(action: RemoveCharacterFromPlay) -> None:
        """Handle removing a family from play if succession fails."""
        family = action.character.get_component(Character).family
        assert family

        family_component = family.get_component(Family)

        if family_component.head is None:
            action.add_reaction(RemoveFamilyFromPlay(family))

    @staticmethod
    def try_pass_power_to_heir(family_head: Entity, family: Entity) -> bool:
        """Attempt to pass power over the family to their heir."""

        heir = family_head.get_component(Character).heir

        if heir is not None:

            heir_character = heir.get_component(Character)

            if heir_character.is_alive and heir_character.family == family:
                BecomeFamilyHead(heir, family).execute()
                return True

        return False

    @staticmethod
    def try_pass_power_to_descendent(family_head: Entity, family: Entity) -> bool:
        """Attempt to pass power to someone in their succession chart."""
        world = family_head.world

        depth_chart = get_succession_depth_chart(family_head)

        if len(depth_chart) > 0:
            for row in depth_chart:
                if row.is_eligible:
                    heir_id = row.character_id
                    heir = world.get_entity(heir_id)
                    heir_character = heir.get_component(Character)

                    if heir_character.is_alive and heir_character.family == family:
                        BecomeFamilyHead(heir, family).execute()
                        return True

        return False

    def on_update(self, world: World) -> None:
        return


class RulerSuccessionSystem(System):
    """Attempts to place the last ruler's heir in power.

    If the system fails to appoint the successor, then the dynasty is ended and the
    thrown is left empty for someone to claim.
    """

    __system_group__ = "LateUpdateSystems"

    def on_start(self, world: World) -> None:
        world.get_resource(ActionSystem).add_listener(
            RemoveCharacterFromPlay, self.handle_succession, "pre"
        )
        world.get_resource(ActionSystem).add_listener(
            RemoveCharacterFromPlay, self.handle_succession_fail, "post"
        )

    @staticmethod
    def handle_succession(action: RemoveCharacterFromPlay) -> None:
        """Handle ruler succession when a character is removed from play."""
        if action.character.has_component(Ruler):
            remove_current_ruler(action.world)

            character_component = action.character.get_component(Character)
            heir = character_component.heir

            if heir is None:
                return

            if not heir.is_active:
                return

            set_current_ruler(action.world, heir)
            heir.get_component(CharacterMetrics).data.directly_inherited_throne = True

    @staticmethod
    def handle_succession_fail(action: RemoveCharacterFromPlay) -> None:
        """Handle case when succession fails."""
        dynasty_tracker = action.world.get_resource(DynastyTracker)
        current_dynasty = dynasty_tracker.current_dynasty

        # Skip there is not a current dynasty
        if current_dynasty is None:
            return

        dynasty_component = current_dynasty.get_component(Dynasty)

        # Skip if the current dynasty has a ruler
        if dynasty_component.current_ruler is not None:
            return

        end_current_dynasty(action.world)

    def on_update(self, world: World) -> None:
        return


class EmptyFamilyCleanUpSystem(System):
    """Removes empty families from play."""

    __system_group__ = "LateUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (family, _) in world.query_components((Family, Active)):
            if len(family.active_members) == 0:
                RemoveFamilyFromPlay(family.entity).execute()


class CharacterBehaviorSystem(System):
    """Family heads and those high on the depth chart take actions."""

    __system_group__ = "UpdateSystems"

    @staticmethod
    def get_acting_characters(world: World) -> list[Entity]:
        """Get all characters who can perform an action this turn."""

        rng = world.get_resource(random.Random)

        family_heads = [
            world.get_entity(uid)
            for uid, _ in world.query_components((HeadOfFamily, Active))
        ]

        acting_characters_set: OrderedSet[Entity] = OrderedSet([*family_heads])

        # for head in family_heads:
        #     depth_chart = get_succession_depth_chart(head)
        #     eligible_character_ids = [
        #         entry.character_id for entry in depth_chart if entry.is_eligible
        #     ]
        #     for uid in eligible_character_ids[:5]:
        #         acting_characters_set.add(world.get_entity(uid))

        acting_characters_list = list(acting_characters_set)
        rng.shuffle(acting_characters_list)

        return acting_characters_list

    @staticmethod
    def update_blackboard_from_sensors(entity: Entity) -> None:
        """Update a character's blackboard using their AI sensors."""
        character_controller = entity.get_component(CharacterController)
        for sensor in character_controller.brain.sensors:
            sensor.evaluate(entity, character_controller.blackboard)

    def on_update(self, world: World) -> None:
        behavior_library = world.get_resource(AIBehaviorLibrary)

        acting_characters = CharacterBehaviorSystem.get_acting_characters(world)

        for character in acting_characters:
            if character.is_active:
                actions: list[AIAction] = []

                character_component = character.get_component(Character)

                character_controller = character.get_component(CharacterController)

                CharacterBehaviorSystem.update_blackboard_from_sensors(character)

                for behavior in behavior_library.iter_behaviors():
                    for potential_action in behavior.get_actions(character):
                        if (
                            character_controller.action_cooldowns[
                                potential_action.get_name()
                            ]
                            <= 0
                            and character_component.influence_points
                            >= potential_action.get_cost()
                        ):
                            actions.append(potential_action)

                if len(actions) > 0:
                    action_scores = score_actions(actions)

                    selected_action: AIAction = (
                        character_controller.brain.action_selection_strategy.choose_action(
                            action_scores
                        )
                    )

                    character_controller.action_cooldowns[
                        selected_action.get_name()
                    ] = selected_action.get_cooldown_time()

                    success = selected_action.execute()

                    if success:
                        character_component.influence_points -= (
                            selected_action.get_cost()
                        )


class FamilyRoleSystem(System):
    """Automatically assign family members to empty family roles."""

    __system_group__ = "LateUpdateSystems"

    def on_update(self, world: World) -> None:
        config = world.get_resource(Config)
        for _, (family_component, _) in world.query_components((Family, Active)):
            # Fill advisor positions
            if len(family_component.advisors) < config.max_advisors_per_family:
                candidates = get_advisor_candidates(family_component.entity)
                if candidates:
                    seats_to_assign = min(
                        config.max_advisors_per_family - len(family_component.advisors),
                        len(candidates),
                    )

                    chosen_candidates = candidates[:seats_to_assign]

                    for family_member in chosen_candidates:
                        assign_family_member_to_roles(
                            family_component.entity,
                            family_member,
                            FamilyRoleFlags.ADVISOR,
                        )

            # Fill warrior positions
            if len(family_component.warriors) < config.max_warriors_per_family:
                candidates = get_warrior_candidates(family_component.entity)
                if candidates:
                    seats_to_assign = min(
                        config.max_warriors_per_family - len(family_component.warriors),
                        len(candidates),
                    )

                    chosen_candidates = candidates[:seats_to_assign]

                    for family_member in chosen_candidates:
                        assign_family_member_to_roles(
                            family_component.entity,
                            family_member,
                            FamilyRoleFlags.WARRIOR,
                        )


class TerritoryRevoltSystem(System):
    """Territories revolt against controlling family.

    When a territory's happiness drops below a given threshold, the territory will
    revolt to remove the controlling family. The head of the controlling family must
    resolve the revolt within a given number of turns or they lose control of the
    territory.
    """

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        config = world.get_resource(Config)

        for _, (territory, happiness, _) in world.query_components(
            (Territory, PopulationHappiness, Active)
        ):
            # Ignore territories with happiness over the threshold
            if happiness.value > config.happiness_revolt_threshold:
                continue

            # Ignore territories that are already revolting
            if territory.entity.has_component(InRevolt):
                continue

            # Ignore territories that are not controlled by a family
            if territory.controlling_family is None:
                continue

            GoIntoRevolt(territory.entity, territory.controlling_family).execute()


class RevoltUpdateSystem(System):
    """Updates existing revolts."""

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        config = world.get_resource(Config)
        current_year = world.get_resource(GameState).year

        for _, (territory, happiness, in_revolt, _) in world.query_components(
            (Territory, PopulationHappiness, InRevolt, Active)
        ):
            years_in_revolt = current_year - in_revolt.start_date

            if years_in_revolt < config.turns_to_quell_revolt:
                continue

            territory.entity.remove_component(InRevolt)
            happiness.base_value = config.base_territory_happiness

            controlling_family = territory.controlling_family

            if controlling_family:
                family_component = controlling_family.get_component(Family)
                family_head = family_component.head

                if family_head:
                    character_component = family_head.get_component(Character)
                    character_component.influence_points -= 500
                    LoseControlOfTerritory(
                        family_head, controlling_family, territory.entity
                    ).execute()

                else:
                    # Just remove the family from being in control
                    set_territory_controlling_family(territory.entity, None)

                increment_prestige_base(controlling_family, -20)


class TerritoryRandomEventSystem(System):
    """Random events can happen to territories to change their happiness.

    Outside of the actions of the controlling family, territories can be subject
    to various random events that affect their happiness state. We select from them
    each month like a deck of cards.

    """

    __system_group__ = "UpdateSystems"

    _random_events: ClassVar[dict[str, tuple[float, Callable[[Entity], None]]]] = {}

    def on_update(self, world: World) -> None:
        rng = world.get_resource(random.Random)

        for _, (territory, _) in world.query_components((Territory, Active)):
            if territory.controlling_family is None:
                continue

            event_name = self.choose_random_event(rng)

            if event_name is None:
                continue

            event_fn = self._random_events[event_name][1]

            event_fn(territory.entity)

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

        def wrapper(fn: Callable[[Entity], None]):
            if relative_frequency <= 0:
                raise ValueError("Relative frequency must be greater than 0")

            cls._random_events[name] = (relative_frequency, fn)

        return wrapper


@TerritoryRandomEventSystem.random_event("nothing", 10)
def nothing_event(_: Entity) -> None:
    """Do Nothing."""
    return


@TerritoryRandomEventSystem.random_event("poor harvest", 0.5)
def poor_harvest_event(territory: Entity) -> None:
    """Poor harvest."""
    current_date = territory.world.get_resource(GameState).year
    happiness_component = territory.get_component(PopulationHappiness)

    happiness_component.base_value -= 10

    _logger.info(
        "[%04d]: %s has suffered a poor harvest.",
        current_date,
        territory.name_with_uid,
    )


@TerritoryRandomEventSystem.random_event("disease", 0.5)
def disease_event(territory: Entity) -> None:
    """Do Nothing."""
    current_date = territory.world.get_resource(GameState).year
    happiness_component = territory.get_component(PopulationHappiness)

    happiness_component.base_value -= 10

    _logger.info(
        "[%04d]: %s has suffered a disease outbreak.",
        current_date,
        territory.name_with_uid,
    )


@TerritoryRandomEventSystem.random_event("bountiful harvest", 0.5)
def bountiful_harvest_event(territory: Entity) -> None:
    """Do Nothing."""
    current_date = territory.world.get_resource(GameState).year
    happiness_component = territory.get_component(PopulationHappiness)

    happiness_component.base_value += 10

    _logger.info(
        "[%04d]: %s had a bountiful harvest.",
        current_date,
        territory.name_with_uid,
    )


class InfluencePointGainSystem(System):
    """Increases the influence points for characters."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        config = world.get_resource(Config)

        for _, (character, _) in world.query_components((Character, Active)):
            influence_gain: int = 1

            if character.entity.has_component(Ruler):
                influence_gain += 5

            if character.entity.has_component(HeadOfFamily):
                influence_gain += 5

            diplomacy = character.entity.get_component(Diplomacy)
            diplomacy_score = int(diplomacy.value)
            if diplomacy_score > 0:
                influence_gain += diplomacy_score // 4

            character.influence_points = min(
                character.influence_points + influence_gain,
                config.influence_points_max,
            )

            character.influence_points = max(0, character.influence_points)

            _logger.debug(
                "[%04d]: %s has %d influence points",
                world.get_resource(GameState).year,
                character.entity.name_with_uid,
                character.influence_points,
            )


class TerritoryInfluencePointBoostSystem(System):
    """The head of a family that controls a territory gets a influence point increase."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (territory, _) in world.query_components((Territory, Active)):
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
        rng = world.get_resource(random.Random)
        chance_get_married = 1.0 / 12.0
        for _, (character, _) in world.query_components((Character, Active)):
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
                    for _, (c, _) in world.query_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and c.sex == Sex.FEMALE
                    and (
                        c.sexual_orientation == SexualOrientation.HETEROSEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                        or c.sexual_orientation == SexualOrientation.ASEXUAL
                    )
                    and c.entity not in character.siblings
                    and c.entity != character.mother
                    and c.entity != character.father
                    and c.entity != character.biological_father
                    and c.entity not in character.children
                    and c.entity not in character.grandchildren
                    and c.entity not in character.grandparents
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
                    for _, (c, _) in world.query_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and c.sex == Sex.MALE
                    and (
                        c.sexual_orientation == SexualOrientation.HETEROSEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                        or c.sexual_orientation == SexualOrientation.ASEXUAL
                    )
                    and c.entity not in character.siblings
                    and c.entity != character.mother
                    and c.entity != character.father
                    and c.entity != character.biological_father
                    and c.entity not in character.children
                    and c.entity not in character.grandchildren
                    and c.entity not in character.grandparents
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
                    for _, (c, _) in world.query_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and c.sex == Sex.MALE
                    and (
                        c.sexual_orientation == SexualOrientation.HOMOSEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                        or c.sexual_orientation == SexualOrientation.ASEXUAL
                    )
                    and c.entity not in character.siblings
                    and c.entity != character.mother
                    and c.entity != character.father
                    and c.entity != character.biological_father
                    and c.entity not in character.children
                    and c.entity not in character.grandchildren
                    and c.entity not in character.grandparents
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
                    for _, (c, _) in world.query_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and c.sex == Sex.FEMALE
                    and (
                        c.sexual_orientation == SexualOrientation.HOMOSEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                        or c.sexual_orientation == SexualOrientation.ASEXUAL
                    )
                    and c.entity not in character.siblings
                    and c.entity != character.mother
                    and c.entity != character.father
                    and c.entity != character.biological_father
                    and c.entity not in character.children
                    and c.entity not in character.grandchildren
                    and c.entity not in character.grandparents
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
                    for _, (c, _) in world.query_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and c.sex == Sex.MALE
                    and (
                        c.sexual_orientation == SexualOrientation.HOMOSEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                    )
                    and c.entity not in character.siblings
                    and c.entity != character.mother
                    and c.entity != character.father
                    and c.entity != character.biological_father
                    and c.entity not in character.children
                    and c != character
                ]

            if (
                character.sexual_orientation == SexualOrientation.BISEXUAL
                and character.sex == Sex.FEMALE
            ):
                # Looking for homosexual or bisexual women
                eligible_singles = [
                    c
                    for _, (c, _) in world.query_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and c.sex == Sex.FEMALE
                    and (
                        c.sexual_orientation == SexualOrientation.HOMOSEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                    )
                    and c.entity not in character.siblings
                    and c.entity != character.mother
                    and c.entity != character.father
                    and c.entity != character.biological_father
                    and c.entity not in character.children
                    and c != character
                ]

            if (
                character.sexual_orientation == SexualOrientation.ASEXUAL
                and character.sex == Sex.FEMALE
            ):
                # Looking for anyone asexual
                eligible_singles = [
                    c
                    for _, (c, _) in world.query_components((Character, Active))
                    if c.spouse is None
                    and c.life_stage >= LifeStage.YOUNG_ADULT
                    and c.life_stage != LifeStage.SENIOR
                    and (
                        c.sexual_orientation == SexualOrientation.ASEXUAL
                        or c.sexual_orientation == SexualOrientation.BISEXUAL
                    )
                    and c.entity not in character.siblings
                    and c.entity != character.mother
                    and c.entity != character.father
                    and c.entity != character.biological_father
                    and c.entity not in character.children
                    and c != character
                ]

            if not eligible_singles:
                continue

            new_spouse = rng.choice(eligible_singles)

            GetMarriedAction(character.entity, new_spouse.entity).execute()


class PregnancyPlaceHolderSystem(System):
    """Handles some subset of married couples having children."""

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        rng = world.get_resource(random.Random)
        current_year = world.get_resource(GameState).year

        for _, (marriage, _) in world.query_components((Marriage, Active)):
            character = marriage.character.get_component(Character)
            spouse = marriage.spouse.get_component(Character)

            if not (character.sex == Sex.FEMALE and spouse.sex == Sex.MALE):
                continue

            if character.entity.has_component(Pregnancy):
                continue

            character_fertility = get_fertility(marriage.character) / 100.0
            spouse_fertility = get_fertility(marriage.spouse) / 100.0

            if character_fertility <= 0 or spouse_fertility <= 0:
                continue

            chance_have_child = (character_fertility + spouse_fertility) / 2

            if rng.random() < chance_have_child:
                character.entity.add_component(
                    Pregnancy(
                        assumed_father=spouse.entity,
                        actual_father=spouse.entity,
                        conception_date=current_year,
                        due_date=current_year + 1,
                    )
                )


class ChildBirthSystem(System):
    """Spawns new children when pregnant characters reach their due dates."""

    def on_update(self, world: World) -> None:
        current_year = world.get_resource(GameState).year

        for _, (character, pregnancy, _) in world.query_components(
            (Character, Pregnancy, Active)
        ):
            if pregnancy.due_date > current_year:
                continue

            GiveBirth(character.entity).execute()


class ActionCooldownSystem(System):
    """Update all active schemes."""

    __system_group__ = "EarlyUpdateSystems"

    def on_update(self, world: World) -> None:
        for _, (brain, _) in world.query_components((CharacterController, Active)):
            for key in brain.action_cooldowns:
                brain.action_cooldowns[key] -= 1


class SchemeUpdateSystems(SystemGroup):
    """Groups all the scheme updaters."""

    __system_group__ = "EarlyUpdateSystems"


class AllianceSchemeUpdateSystem(System):
    """Updates all alliance schemes."""

    __system_group__ = "SchemeUpdateSystems"

    def on_update(self, world: World) -> None:
        current_date = world.get_resource(GameState).year

        for _, (scheme, _, _) in world.query_components(
            (Scheme, AllianceScheme, Active)
        ):
            if not scheme.initiator.is_active:
                scheme.is_valid = False
                destroy_alliance_scheme(scheme.entity)
                continue

            if scheme.is_valid is False:
                destroy_alliance_scheme(scheme.entity)
                continue

            elapsed_years = current_date - scheme.start_date

            if elapsed_years >= scheme.required_time:
                # Check that other people have joined the scheme for the alliance to be
                # created. Otherwise, this scheme fails
                if len(scheme.members) > 1:

                    # Need to get all the families of scheme members
                    alliance_families: list[Entity] = []
                    for member in scheme.members:
                        character_component = member.get_component(Character)
                        if character_component.family is None:
                            raise RuntimeError("Alliance member is missing family.")
                        alliance_families.append(character_component.family)

                    start_alliance(*alliance_families)
                    CreateAllianceAction(scheme.initiator).execute()

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
                        Prestige
                    ).base_value += 30

                    scheme.initiator.get_component(
                        CharacterMetrics
                    ).data.num_alliances_founded += 1

                else:
                    scheme.initiator.get_component(
                        CharacterMetrics
                    ).data.num_failed_alliance_attempts += 1

                scheme.is_valid = False
                destroy_alliance_scheme(scheme.entity)


class WarSchemeUpdateSystem(System):
    """Updates all active war schemes."""

    __system_group__ = "SchemeUpdateSystems"

    @staticmethod
    def are_in_same_alliance(character_a: Entity, character_b: Entity) -> bool:
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
    def get_family(character: Entity) -> Entity:
        """Get the reference to a character's family."""
        character_family = character.get_component(Character).family
        if character_family is None:
            raise RuntimeError(f"{character.name_with_uid} does not have a family.")
        return character_family

    @staticmethod
    def get_alliance(family: Entity) -> Entity:
        """Get  reference to a family's alliance."""
        family_alliance = family.get_component(Family).alliance
        if family_alliance is None:
            raise RuntimeError(f"{family.name_with_uid} does not have an alliance.")
        return family_alliance

    @staticmethod
    def add_alliance_members_as_allies(
        war: Entity, character: Entity, role: WarRole
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
        current_date = world.get_resource(GameState).year

        for _, (scheme, war_scheme, _) in world.query_components(
            (Scheme, WarScheme, Active)
        ):
            # Cancel the scheme if has been invalidated by an external system
            if not war_scheme.aggressor.is_active or not war_scheme.defender.is_active:
                scheme.is_valid = False
                destroy_war_scheme(scheme.entity)
                continue

            if scheme.is_valid is False:
                destroy_war_scheme(scheme.entity)
                continue

            # Cancel the scheme if the initiator and scheme target belong to the
            # same alliance
            if self.are_in_same_alliance(scheme.initiator, war_scheme.defender):
                scheme.is_valid = False
                destroy_war_scheme(scheme.entity)
                continue

            elapsed_years = current_date - scheme.start_date

            if elapsed_years >= scheme.required_time:
                aggressor_family = self.get_family(scheme.initiator)
                defender_family = self.get_family(war_scheme.defender)

                scheme.initiator.get_component(CharacterMetrics).data.num_wars += 1
                war_scheme.defender.get_component(CharacterMetrics).data.num_wars += 1
                scheme.initiator.get_component(
                    CharacterMetrics
                ).data.num_wars_started += 1
                scheme.initiator.get_component(
                    CharacterMetrics
                ).data.date_of_last_declared_war = current_date

                war = start_war(aggressor_family, defender_family, war_scheme.territory)

                self.add_alliance_members_as_allies(
                    war, scheme.initiator, WarRole.AGGRESSOR_ALLY
                )

                self.add_alliance_members_as_allies(
                    war, war_scheme.defender, WarRole.DEFENDER_ALLY
                )

                DeclareWar(
                    scheme.initiator, war_scheme.defender, war_scheme.territory
                ).execute()

                scheme.is_valid = False
                destroy_war_scheme(scheme.entity)


class CoupSchemeUpdateSystem(System):
    """Updates all active war schemes."""

    __system_group__ = "SchemeUpdateSystems"

    def on_update(self, world: World) -> None:
        current_date = world.get_resource(GameState).year
        rng = world.get_resource(random.Random)

        for _, (scheme, coup_scheme, _) in world.query_components(
            (Scheme, CoupScheme, Active)
        ):
            if not scheme.initiator.is_active or not coup_scheme.target.is_active:
                scheme.is_valid = False
                destroy_coup_scheme(scheme.entity)
                continue

            if scheme.is_valid is False:
                destroy_coup_scheme(scheme.entity)
                continue

            if not coup_scheme.target.is_active:
                destroy_coup_scheme(scheme.entity)
                continue

            current_ruler = get_current_ruler(world)

            if current_ruler is None:
                scheme.is_valid = False
                continue

            elapsed_years = current_date - scheme.start_date

            if elapsed_years >= scheme.required_time:
                # Check that other people have joined the scheme for the alliance to be
                # created. Otherwise, this scheme fails
                if len(scheme.members) > 2:

                    # Kill the current ruler.

                    OverthrowRulerAction(scheme.initiator, current_ruler).execute()

                    ruler_family = current_ruler.get_component(Character).family

                    current_ruler.get_component(Character).killed_by = scheme.initiator

                    DieAction(current_ruler, cause="assassination").execute()
                    end_current_dynasty(world)

                    if ruler_family is not None:
                        # Remove the rulers family from being in control of their home
                        # base
                        family_component = ruler_family.get_component(Family)

                        for territory in family_component.controlled_territories:
                            set_territory_controlling_family(territory, None)

                    for member in scheme.members:
                        member_character_comp = member.get_component(Character)

                        assert member_character_comp.family

                        member_character_comp.family.get_component(
                            Prestige
                        ).base_value += 50

                        if member != scheme.initiator:
                            get_relationship(scheme.initiator, member).get_component(
                                Opinion
                            ).base_value += 30

                    ClaimThroneAction(scheme.initiator).execute()

                scheme.is_valid = False
                destroy_coup_scheme(scheme.entity)

            else:

                # Check if the coup is discovered by the royal family
                intrigue_score = get_intrigue_skill(scheme.initiator)

                # Nothing happens
                if (rng.random() * 0.75) < intrigue_score / 100.0:
                    continue

                DiscoverCoupScheme(current_ruler, coup_scheme).execute()

                # They are discovered and put to death
                for member in scheme.members:
                    member_character_comp = member.get_component(Character)

                    # Reduce traitor family prestige
                    assert member_character_comp.family

                    member_character_comp.family.get_component(
                        Prestige
                    ).base_value -= 50

                    # Execute traitor
                    member_character_comp.killed_by = coup_scheme.target
                    SentenceToDeath(current_ruler, member, "treason").execute()

                scheme.is_valid = False
                destroy_coup_scheme(scheme.entity)


class WarUpdateSystem(System):
    """Updates all active wars."""

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        rng = world.get_resource(random.Random)

        for _, (war, _) in world.query_components((War, Active)):

            # Check that the family heads are alive
            aggressor_family_head = war.aggressor.get_component(Family).head
            defender_family_head = war.defender.get_component(Family).head

            if aggressor_family_head is None or defender_family_head is None:
                war.entity.deactivate()
                end_war(war.entity, None)
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
            casualties: list[Entity] = []

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
                    "[%04d]: The %s family defeated the %s family and has taken control "
                    "of the %s territory.",
                    world.get_resource(GameState).year,
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

                war.aggressor.get_component(Prestige).base_value += 40
                war.defender.get_component(Prestige).base_value -= 20

                end_war(war.entity, war.aggressor)

            else:
                # Defender wins the battle
                # Aggressor loses influence points

                # TODO: Fire and log events for winning and losing wars
                _logger.info(
                    "[%04d]: The %s family failed to defeat the %s family over control "
                    "of the %s territory.",
                    world.get_resource(GameState).year,
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

                war.aggressor.get_component(Prestige).base_value -= 50
                war.defender.get_component(Prestige).base_value += 35

                end_war(war.entity, war.defender)

            # Kill off the casualties
            for character in casualties:
                DieAction(character, cause="war").execute()


class FamilyRefillSystem(System):
    """Spawns new families in territories that have too few families."""

    __system_group__ = "UpdateSystems"

    def on_update(self, world: World) -> None:
        current_date = world.get_resource(GameState).year
        for _, (territory, _) in world.query_components((Territory, Active)):
            if len(territory.families) < 3:
                family = spawn_family(world, FamilyGenOptions(spawn_members=True))
                family_component = family.get_component(Family)
                set_family_home_base(family, territory.entity)
                family_component.territories_present_in.add(territory.entity)
                _logger.info(
                    "[%04d]: The %s family has risen to prominence in the %s territory.",
                    current_date,
                    family.name_with_uid,
                    territory.entity.name_with_uid,
                )


class HeirDeclarationSystem(System):
    """Family heads missing an heir will try to name an heir."""

    __system_group__ = "UpdateSystems"

    @staticmethod
    def get_oldest_child(character: Character) -> Optional[Entity]:
        """Get the oldest living child of the character who is in the same family."""

        child_list: list[tuple[Entity, float]] = []

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
        current_date = world.get_resource(GameState).year

        for _, (character, _, _) in world.query_components(
            (Character, HeadOfFamily, Active)
        ):
            if character.heir is not None:
                continue

            oldest_child = HeirDeclarationSystem.get_oldest_child(character)

            if oldest_child:
                oldest_child_character_comp = oldest_child.get_component(Character)
                set_heir(character.entity, oldest_child)
                oldest_child_character_comp.heir_to = character.entity
                _logger.info(
                    "[%04d]: %s declared %s their heir.",
                    current_date,
                    character.entity.name_with_uid,
                    oldest_child.name_with_uid,
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
    def get_orphans_in_family(character_component: Character) -> list[Entity]:
        """Get all orphans in the family."""

        family = character_component.family
        if family is None:
            return []

        orphans: list[Entity] = []
        family_component = family.get_component(Family)
        for member in family_component.active_members:
            member_character = member.get_component(Character)
            if OrphanAdoptionSystem.is_orphan(member_character):
                orphans.append(member)

        return orphans

    def on_update(self, world: World) -> None:
        rng = world.get_resource(random.Random)
        current_date = world.get_resource(GameState).year

        for _, (character, _, _) in world.query_components(
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
                    "[%04d]: %s adopted %s.",
                    current_date,
                    character.entity.name_with_uid,
                    chosen_orphan.name_with_uid,
                )


class MapGenerationSystem(System):
    """Initializes the world map by generating territories."""

    __system_group__ = "InitializationSystems"

    def on_update(self, world: World) -> None:
        generate_world_map(world)
        _logger.info("Generating map and territories.")
        world.get_resource(ActionSystem).perform(GenerateMap(world))

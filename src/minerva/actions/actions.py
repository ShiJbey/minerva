"""Concrete Action implementations."""

from __future__ import annotations

import logging

from minerva.actions.base_types import AIAction, Scheme
from minerva.actions.scheme_helpers import add_member_to_scheme
from minerva.characters.components import Character, Family, HeadOfFamily
from minerva.characters.helpers import remove_character_from_play, set_character_alive
from minerva.characters.metric_data import CharacterMetrics
from minerva.characters.war_data import Alliance
from minerva.characters.war_helpers import (
    create_alliance_scheme,
    create_coup_scheme,
    create_war_scheme,
    end_alliance,
    join_alliance,
)
from minerva.config import Config
from minerva.datetime import SimDate
from minerva.ecs import Active, GameObject
from minerva.life_events.aging import DeathEvent
from minerva.life_events.events import (
    AttemptingFormAllianceEvent,
    DisbandedAllianceEvent,
    ExpandedFamilyTerritoryEvent,
    ExpandedTerritoryEvent,
    FamilyJoinedAllianceEvent,
    GiveBackToSmallFolkEvent,
    GrowPoliticalInfluenceEvent,
    JoinAllianceSchemeEvent,
    JoinCoupSchemeEvent,
    JoinedAllianceEvent,
    QuellRevoltEvent,
    StartCoupSchemeEvent,
    StartWarSchemeEvent,
    TakeOverTerritoryEvent,
    TaxTerritoryEvent,
)
from minerva.relationships.base_types import Opinion
from minerva.relationships.helpers import get_relationship
from minerva.world_map.components import InRevolt, PopulationHappiness, Territory
from minerva.world_map.helpers import (
    increment_political_influence,
    set_territory_controlling_family,
)

_logger = logging.getLogger(__name__)


class IdleAction(AIAction):
    """Character does nothing."""

    def __init__(self, performer: GameObject) -> None:
        super().__init__(performer, "Idle")

    def execute(self) -> bool:
        current_date = self.world.resources.get_resource(SimDate)

        _logger.debug(
            "[%s]: %s is idle.",
            current_date.to_iso_str(),
            self.performer.name_with_uid,
        )

        return True


class GiveBackToTerritoryAction(AIAction):
    """An instance of a get married action."""

    __slots__ = ("family", "territory")

    family: GameObject
    territory: GameObject

    def __init__(
        self, performer: GameObject, family: GameObject, territory: GameObject
    ) -> None:
        super().__init__(performer, "GiveBackToTerritory")
        self.context["family"] = family
        self.context["territory"] = territory
        self.family = family
        self.territory = territory

    def execute(self) -> bool:
        increment_political_influence(self.territory, self.family, 5)

        self.territory.get_component(PopulationHappiness).base_value += 5

        GiveBackToSmallFolkEvent(self.performer, self.territory).log_event()

        return True


class GrowPoliticalInfluenceAction(AIAction):
    """A family head grows their political influence in a territory."""

    __slots__ = ("family", "territory")

    family: GameObject
    territory: GameObject

    def __init__(
        self, performer: GameObject, family: GameObject, territory: GameObject
    ) -> None:
        super().__init__(performer, "GrowPoliticalInfluence")
        self.context["family"] = family
        self.context["territory"] = territory
        self.family = family
        self.territory = territory

    def execute(self) -> bool:
        increment_political_influence(self.territory, self.family, 15)

        GrowPoliticalInfluenceEvent(
            self.performer, self.family, self.territory
        ).log_event()

        return True


class GetMarriedAction(AIAction):
    """An instance of a get married action."""

    def __init__(self, performer: GameObject, partner: GameObject) -> None:
        super().__init__(performer, "GetMarried")
        self.context["partner"] = partner

    def execute(self) -> bool:
        return True


class DieAction(AIAction):
    """Instance of an action where a character dies."""

    def __init__(
        self, performer: GameObject, cause_of_death: str = "", pass_crown: bool = True
    ) -> None:
        super().__init__(performer, "Die")
        self.pass_crown = pass_crown
        self.cause_of_death = cause_of_death

    def execute(self) -> bool:
        """Have a character die."""
        character = self.context.character

        set_character_alive(character, False)
        character.deactivate()

        DeathEvent(character, cause=self.cause_of_death).log_event()

        remove_character_from_play(character, pass_crown=self.pass_crown)

        return True


class SendGiftAction(AIAction):
    """One family head sends a gift to another."""

    __slots__ = ("recipient",)

    recipient: GameObject

    def __init__(self, performer: GameObject, recipient: GameObject) -> None:
        super().__init__(performer, "SendGift")
        self.context["recipient"] = recipient
        self.performer = performer
        self.recipient = recipient

    def execute(self) -> bool:
        world = self.context.world
        current_date = world.resources.get_resource(SimDate)

        get_relationship(self.recipient, self.performer).get_component(
            Opinion
        ).base_value += 10

        _logger.info(
            "[%s]: %s sent a gift to %s.",
            current_date.to_iso_str(),
            self.performer.name_with_uid,
            self.recipient.name_with_uid,
        )

        return True


class SendAidAction(AIAction):
    """One family head sends a aid to another during a revolt."""

    performer: GameObject
    recipient: GameObject

    def __init__(self, performer: GameObject, recipient: GameObject) -> None:
        super().__init__(performer, "SendGift")
        self.context["recipient"] = recipient
        self.performer = performer
        self.recipient = recipient

    def execute(self) -> bool:
        world = self.context.world
        current_date = world.resources.get_resource(SimDate)

        self.recipient.get_component(Character).influence_points += 50

        get_relationship(self.recipient, self.performer).get_component(
            Opinion
        ).base_value += 20

        _logger.info(
            "[%s]: %s sent aid to %s.",
            current_date.to_iso_str(),
            self.performer.name_with_uid,
            self.recipient.name_with_uid,
        )

        return True


class ExtortTerritoryOwnersAction(AIAction):
    """Ruler extorts all the families that control territories."""

    def __init__(self, performer: GameObject) -> None:
        super().__init__(performer, "ExtortTerritoryOwners")

    def execute(self) -> bool:
        world = self.context.world
        current_date = world.resources.get_resource(SimDate)

        for _, (territory, _) in world.get_components((Territory, Active)):
            if territory.controlling_family:
                family_component = territory.controlling_family.get_component(Family)
                if family_component.head:
                    family_head = family_component.head
                    family_head.get_component(Character).influence_points -= 20
                    get_relationship(family_head, self.performer).get_component(
                        Opinion
                    ).base_value -= 10

        _logger.info(
            "[%s]: %s extorted the land controlling families.",
            current_date.to_iso_str(),
            self.performer.name_with_uid,
        )

        return True


class ExtortLocalFamiliesAction(AIAction):
    """Family controlling a territory extorts other families residing there."""

    def __init__(self, performer: GameObject) -> None:
        super().__init__(performer, "ExtortLocalFamilies")

    def execute(self) -> bool:
        world = self.context.world
        current_date = world.resources.get_resource(SimDate)
        family_head_component = self.performer.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        for territory in family_component.territories:
            territory_component = territory.get_component(Territory)
            if territory_component.controlling_family == family_component.gameobject:
                for other_family in territory_component.families:
                    if other_family == family_component.gameobject:
                        continue

                    other_family_component = other_family.get_component(Family)
                    if other_family_component.head:
                        other_family_head = other_family_component.head
                        other_family_head.get_component(Character).influence_points -= 5
                        get_relationship(
                            other_family_head, self.performer
                        ).get_component(Opinion).base_value -= 10
                        self.performer.get_component(Character).influence_points += 5

        _logger.info(
            "[%s]: %s extorted the families in their territories.",
            current_date.to_iso_str(),
            self.performer.name_with_uid,
        )

        return True


class QuellRevoltAction(AIAction):
    """A parameterized instance of a quell revolt action."""

    __slots__ = ("territory",)

    territory: GameObject

    def __init__(self, performer: GameObject, territory: GameObject) -> None:
        super().__init__(performer, "QuellRevolt")
        self.context["territory"] = territory
        self.territory = territory

    def execute(self) -> bool:
        config = self.context.world.resources.get_resource(Config)

        self.territory.remove_component(InRevolt)

        population_happiness = self.territory.get_component(PopulationHappiness)

        population_happiness.base_value = config.base_territory_happiness

        self.performer.get_component(CharacterMetrics).data.num_revolts_quelled += 1

        QuellRevoltEvent(self.performer, self.territory).log_event()

        return True


class TaxTerritoryAction(AIAction):
    """An instance of a get married action."""

    __slots__ = ("territory",)

    territory: GameObject

    def __init__(self, performer: GameObject, territory: GameObject) -> None:
        super().__init__(performer, "TaxTerritory")
        self.context["territory"] = territory
        self.territory = territory

    def execute(self) -> bool:
        character_component = self.context.character.get_component(Character)
        character_component.influence_points += 250

        self.territory.get_component(PopulationHappiness).base_value -= 20

        TaxTerritoryEvent(self.performer, self.territory)

        return True


class StartWarSchemeAction(AIAction):
    """Action instance data for starting a war scheme against a specific person."""

    __slots__ = ("target", "territory")

    target: GameObject
    territory: GameObject

    def __init__(
        self,
        performer: GameObject,
        target: GameObject,
        territory: GameObject,
    ) -> None:
        super().__init__(performer, "StartWarScheme")
        self.territory = territory
        self.target = target
        self.context["aggressor"] = performer
        self.context["target"] = target
        self.context["territory"] = territory

    def execute(self) -> bool:
        create_war_scheme(
            initiator=self.performer, target=self.target, territory=self.territory
        )

        StartWarSchemeEvent(
            subject=self.performer,
            target=self.target,
            territory=self.territory,
        ).log_event()

        return True


class StartCoupSchemeAction(AIAction):
    """Instance data for starting a scheme to overthrow the royal family."""

    __slots__ = ("target",)

    target: GameObject

    def __init__(self, initiator: GameObject, target: GameObject) -> None:
        super().__init__(initiator, "StartCoupScheme")
        self.context["initiator"] = initiator
        self.context["target"] = target
        self.target = target

    def execute(self) -> bool:
        create_coup_scheme(initiator=self.performer, target=self.target)

        self.performer.get_component(CharacterMetrics).data.num_coups_planned += 1

        StartCoupSchemeEvent(self.performer, self.target)

        return True


class JoinCoupSchemeAction(AIAction):
    """A character joins someones coup scheme."""

    __slots__ = ("scheme",)

    scheme: GameObject

    def __init__(self, performer: GameObject, scheme: GameObject) -> None:
        super().__init__(performer, "JoinCoupScheme")
        self.context["scheme"] = scheme
        self.scheme = scheme

    def execute(self) -> bool:
        add_member_to_scheme(self.scheme, self.performer)

        JoinCoupSchemeEvent(
            self.performer, self.scheme.get_component(Scheme).initiator
        ).log_event()

        return True


class JoinAllianceSchemeAction(AIAction):
    """A character joins someones alliance scheme."""

    __slots__ = ("scheme",)

    scheme: GameObject

    def __init__(self, performer: GameObject, scheme: GameObject) -> None:
        super().__init__(performer, "JoinAllianceScheme")
        self.context["scheme"] = scheme
        self.scheme = scheme

    def execute(self) -> bool:
        add_member_to_scheme(self.scheme, self.performer)

        JoinAllianceSchemeEvent(
            self.performer,
            self.scheme.get_component(Scheme).initiator,
        ).log_event()

        return True


class StartAllianceSchemeAction(AIAction):
    """Action instance data for starting a war scheme against a specific person."""

    def __init__(
        self,
        performer: GameObject,
    ) -> None:
        super().__init__(performer, "StartAllianceScheme")

    def execute(self) -> bool:
        create_alliance_scheme(self.performer)

        AttemptingFormAllianceEvent(self.performer).log_event()

        return True


class JoinExistingAllianceAction(AIAction):
    """Join someones existing alliance."""

    __slots__ = ("alliance",)

    alliance: GameObject

    def __init__(self, performer: GameObject, alliance: GameObject) -> None:
        super().__init__(performer, "JoinExistingAlliance")
        self.context["alliance"] = alliance
        self.alliance = alliance

    def execute(self) -> bool:
        family = self.performer.get_component(Character).family

        if family is None:
            raise RuntimeError(f"{self.performer.name_with_uid} is missing a family.")

        join_alliance(alliance=self.alliance, family=family)

        JoinedAllianceEvent(subject=self.performer, alliance=self.alliance).log_event()
        FamilyJoinedAllianceEvent(subject=family, alliance=self.alliance).log_event()

        return True


class DisbandAllianceAction(AIAction):
    """Disband an alliance."""

    __slots__ = ("alliance",)

    alliance: GameObject

    def __init__(self, performer: GameObject, alliance: GameObject) -> None:
        super().__init__(performer, "DisbandAlliance")
        self.context["alliance"] = alliance
        self.alliance = alliance

    def execute(self) -> bool:
        family_head_component = self.performer.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        alliance_component = self.alliance.get_component(Alliance)

        founding_family = alliance_component.founder_family

        for member_family in alliance_component.member_families:
            if member_family == family_component.gameobject:
                continue

            member_family_component = member_family.get_component(Family)

            if member_family_component.head is not None:
                get_relationship(
                    member_family_component.head, self.performer
                ).get_component(Opinion).base_value -= 20

        end_alliance(self.alliance)

        self.performer.get_component(CharacterMetrics).data.num_alliances_disbanded += 1

        DisbandedAllianceEvent(
            subject=self.performer, founding_family=founding_family
        ).log_event()

        return True


class ExpandIntoTerritoryAction(AIAction):
    """."""

    def __init__(self, family_head: GameObject, territory: GameObject) -> None:
        super().__init__(family_head, "ExpandIntoTerritory")
        self.context["family_head"] = family_head
        self.context["territory"] = territory

    def execute(self) -> bool:
        family_head: GameObject = self.context["family_head"]
        territory: GameObject = self.context["territory"]

        family_head_component = family_head.get_component(HeadOfFamily)

        territory_component = territory.get_component(Territory)
        territory_component.political_influence[family_head_component.family] = 50
        family_head_component.family.get_component(Family).territories.add(territory)

        ExpandedTerritoryEvent(
            subject=family_head_component.family,
            territory=territory,
        ).log_event()

        ExpandedFamilyTerritoryEvent(
            subject=family_head,
            family=family_head_component.family,
            territory=territory,
        ).log_event()

        return True


class SeizeTerritoryAction(AIAction):
    """."""

    def __init__(self, performer: GameObject, territory: GameObject) -> None:
        super().__init__(performer, "SeizeTerritory")
        self.context["family_head"] = performer
        self.context["territory"] = territory

    def execute(self) -> bool:
        family_head: GameObject = self.context["family_head"]
        territory: GameObject = self.context["territory"]

        family_head_component = family_head.get_component(HeadOfFamily)

        set_territory_controlling_family(territory, family_head_component.family)

        self.performer.get_component(CharacterMetrics).data.num_territories_taken += 1

        TakeOverTerritoryEvent(
            subject=family_head,
            territory=territory,
            family=family_head_component.family,
        ).log_event()

        return True

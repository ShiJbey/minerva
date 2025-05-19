"""Concrete Action implementations."""

from __future__ import annotations

import random

from minerva.actions.base_types import AIAction, get_proclivity_score
from minerva.actions.scheme_types import (
    AllianceScheme,
    AllianceSchemeMember,
    CoupScheme,
    SchemeManager,
)
from minerva.characters.components import (
    Character,
    Family,
    HeadOfFamily,
    LifeStage,
    Pregnancy,
    Sex,
)
from minerva.characters.helpers import (
    RemoveCharacterFromPlay,
    get_fertility,
    increment_fertility_base,
    increment_prestige_base,
    merge_family_with,
    remove_heir,
    set_character_alive,
    set_character_biological_father,
    set_character_birth_family,
    set_character_death_year,
    set_character_family,
    set_character_father,
    set_character_life_stage,
    set_character_mother,
    set_family_head,
    set_relation_child,
    set_relation_sibling,
    start_marriage,
    update_grandparent_relations,
)
from minerva.characters.metric_data import CharacterMetrics
from minerva.characters.succession_helpers import start_new_dynasty
from minerva.characters.war_data import Alliance
from minerva.characters.war_helpers import (
    add_family_to_alliance,
    create_coup_scheme,
    create_war_scheme,
    remove_family_from_alliance,
    start_alliance,
)
from minerva.config import Config
from minerva.ecs import Active, Entity
from minerva.events import (
    BecomeAdolescentEvent,
    BecomeAdultEvent,
    BecomeChildEvent,
    BecomeFamilyHeadEvent,
    BecomeSeniorEvent,
    BecomeYoungAdultEvent,
    CheatOnSpouseEvent,
    CoupSchemeDiscoveredEvent,
    DeathEvent,
    DeclareWarEvent,
    ExtortLocalFamiliesEvent,
    ExtortTerritoryOwnersEvent,
    GiveBirthEvent,
    GiveToTerritoriesEvent,
    JoinAllianceEvent,
    JoinCoupSchemeEvent,
    LeaveAllianceEvent,
    LoseControlOfTerritoryEvent,
    MarriageEvent,
    QuellRevoltEvent,
    RevoltEvent,
    SeizeTerritoryEvent,
    SendAidEvent,
    SendGiftEvent,
    SentenceToDeathEvent,
    StartAllianceEvent,
    StartCoupSchemeEvent,
    StartWarSchemeEvent,
    TaxTerritoriesEvent,
    UsurpThroneEvent,
    WarWonEvent,
)
from minerva.game_action import GameAction
from minerva.game_state import GameState
from minerva.pcg.character import spawn_baby_from
from minerva.relationships.helpers import IncrementAttraction, IncrementOpinion
from minerva.traits.helpers import add_trait
from minerva.world_map.components import InRevolt, Territory
from minerva.world_map.helpers import (
    SetTerritoryControllingFamily,
    UnsetControllingFamily,
    increment_happiness_base,
    set_happiness_base,
)


class IncrementPopulationHappiness(GameAction):
    """Set the happiness level of a territory's populace."""

    __slots__ = ("territory", "amount")

    territory: Entity
    amount: int

    def __init__(self, territory: Entity, amount: int) -> None:
        super().__init__(territory.world)
        self.territory = territory
        self.amount = amount

    def on_execute(self) -> None:
        increment_happiness_base(self.territory, self.amount)


class GiveToTerritoriesAction(AIAction):
    """A family head increases the happiness level of all their territories."""

    __action_cost__ = 100
    __action_cooldown__ = 4
    __action_tags__ = ["generosity", "give_back", "beneficent"]

    __slots__ = ("character", "family", "territory")

    def __init__(self, character: Entity, family: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.family = family
        self.context["family"] = family

    def on_execute(self) -> None:
        """Perform the self."""
        family_component = self.family.get_component(Family)

        for territory in family_component.controlled_territories:
            self.add_reaction(IncrementPopulationHappiness(territory, 5))

        GiveToTerritoriesEvent(self.character).log_event()


class TryGetMarriedAction(AIAction):
    """A character decides if they generally want to get married."""

    __slots__ = ("character",)

    character: Entity

    def __init__(self, character: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.context["character"] = character.name_with_uid

    def on_execute(self) -> None:
        # This action intentionally does nothing. It is a placeholder for
        # organizing proclivities. This execute method will never be called.
        return


class GetMarriedAction(AIAction):
    """Two characters get married.

    The spouse always marries into the initiator's family.
    """

    __action_cost__ = 0
    __action_cooldown__ = 0
    __action_tags__ = ["romance", "marriage"]

    __slots__ = ("character", "spouse")

    character: Entity
    """The character that initiated the action."""
    spouse: Entity
    """Character being married to the initiator."""

    def __init__(self, character: Entity, spouse: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.spouse = spouse
        self.context["spouse"] = spouse

    def on_execute(self) -> None:
        character = self.character.get_component(Character)
        new_spouse = self.spouse.get_component(Character)

        start_marriage(character_a=self.character, character_b=self.spouse)

        # Now handle any family logistics

        # Case 1: The character is head of their family and their new spouse is
        # the head of their family
        if self.character.has_component(HeadOfFamily) and self.spouse.has_component(
            HeadOfFamily
        ):
            # Join the families into a single entity
            family_a = character.family
            family_b = new_spouse.family
            assert family_a is not None
            assert family_b is not None
            set_family_head(family_b, None)
            merge_family_with(family_b, family_a)

            # new spouse loses all their heirs
            if new_spouse.heir is not None:
                remove_heir(new_spouse.entity)

        # Case 2: The character is head of their family and their spouse is not
        if character.entity.has_component(
            HeadOfFamily
        ) and not new_spouse.entity.has_component(HeadOfFamily):
            family_a = character.family
            assert family_a is not None
            set_character_family(new_spouse.entity, family_a)

            # new spouse loses heir eligibility
            if new_spouse.heir_to is not None:
                remove_heir(new_spouse.heir_to)

        # Case 3: The character is not head of their family and their spouse is
        if not character.entity.has_component(
            HeadOfFamily
        ) and new_spouse.entity.has_component(HeadOfFamily):
            family_a = character.family
            family_b = new_spouse.family
            assert family_a is not None
            assert family_b is not None
            set_family_head(family_b, None)
            set_character_family(new_spouse.entity, family_a)

            # character loses heir eligibility
            if new_spouse.heir_to is not None:
                remove_heir(new_spouse.heir_to)

        # Case 4: Neither character is head of their family.
        if not character.entity.has_component(
            HeadOfFamily
        ) and not new_spouse.entity.has_component(HeadOfFamily):
            family_a = character.family
            assert family_a is not None
            set_character_family(new_spouse.entity, family_a)

            # new spouse loses heir eligibility
            if new_spouse.heir_to is not None:
                remove_heir(new_spouse.heir_to)

        MarriageEvent(self.character, self.spouse).log_event()
        MarriageEvent(self.spouse, self.character).log_event()


class BecomeSeniorAction(AIAction):
    """Initiator becomes a senior."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character)
        self.character = character

    def on_execute(self) -> None:
        """Perform the self."""
        set_character_life_stage(self.character, LifeStage.SENIOR)
        BecomeSeniorEvent(self.character).log_event()


class BecomeAdultAction(AIAction):
    """Initiator becomes an adult."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character)
        self.character = character

    def on_execute(self) -> None:
        set_character_life_stage(self.character, LifeStage.ADULT)
        BecomeAdultEvent(self.character).log_event()


class BecomeYoungAdultAction(AIAction):
    """Initiator becomes a young adult."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character)
        self.character = character

    def on_execute(self) -> None:
        set_character_life_stage(self.character, LifeStage.YOUNG_ADULT)
        BecomeYoungAdultEvent(self.character).log_event()


class BecomeAdolescentAction(AIAction):
    """Initiator becomes an adolescent."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character)
        self.character = character

    def on_execute(self) -> None:
        set_character_life_stage(self.character, LifeStage.ADOLESCENT)
        BecomeAdolescentEvent(self.character).log_event()


class BecomeChildAction(AIAction):
    """Initiator becomes a child."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character)
        self.character = character

    def on_execute(self) -> None:
        set_character_life_stage(self.character, LifeStage.CHILD)
        BecomeChildEvent(self.character).log_event()


class DieAction(AIAction):
    """Instance of an action where a character dies."""

    __slots__ = ("character", "cause")

    character: Entity
    cause: str

    def __init__(self, character: Entity, cause: str = "") -> None:
        super().__init__(character)
        self.character = character
        self.cause = cause

    def on_execute(self) -> None:
        set_character_alive(self.character, False)

        set_character_death_year(
            self.character, self.world.get_resource(GameState).year
        )

        RemoveCharacterFromPlay(self.character).execute()

        DeathEvent(self.character, self.cause).log_event()


class SendGiftAction(AIAction):
    """One family head sends a gift to another."""

    __action_cost__ = 150
    __action_cooldown__ = 2
    __action_tags__ = ["generosity", "diplomacy"]

    __slots__ = ("character", "recipient")

    character: Entity
    recipient: Entity

    def __init__(self, character: Entity, recipient: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.recipient = recipient

    def on_execute(self) -> None:

        self.add_reaction(IncrementOpinion(self.recipient, self.character, 10))
        SendGiftEvent(self.character, self.recipient).log_event()


class SendAidAction(AIAction):
    """One family head sends a aid to another during a revolt."""

    __action_cost__ = 150
    __action_cooldown__ = 1
    __action_tags__ = ["diplomacy"]

    __slots__ = ("character", "recipient")

    character: Entity
    recipient: Entity

    def __init__(self, character: Entity, recipient: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.recipient = recipient

    def on_execute(self) -> None:

        performer_character_comp = self.character.get_component(Character)

        if performer_character_comp.family:
            increment_prestige_base(performer_character_comp.family, 1)

        self.recipient.get_component(Character).influence_points += 50

        self.add_reaction(IncrementOpinion(self.recipient, self.character, 20))

        SendAidEvent(self.character, self.recipient).log_event()


class ExtortTerritoryOwnersAction(AIAction):
    """Ruler extorts all the families that control territories."""

    __action_cost__ = 200
    __action_cooldown__ = 1

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character)
        self.character = character

    def on_execute(self) -> None:

        for _, (territory, _) in self.world.query_components((Territory, Active)):
            if territory.controlling_family:
                family_component = territory.controlling_family.get_component(Family)
                if family_component.head:
                    family_head = family_component.head
                    family_head.get_component(Character).influence_points -= 20
                    self.add_reaction(
                        IncrementOpinion(family_head, self.character, -10)
                    )

        ExtortTerritoryOwnersEvent(self.character).log_event()


class ExtortLocalFamiliesAction(AIAction):
    """Family controlling a territory extorts other families residing there."""

    __action_cost__ = 200
    __action_cooldown__ = 1

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character)
        self.character = character

    def on_execute(self) -> None:

        family_head_component = self.character.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        for territory in family_component.controlled_territories:
            territory_component = territory.get_component(Territory)

            for other_family in territory_component.families:
                if other_family == family_component.entity:
                    continue

                other_family_component = other_family.get_component(Family)
                if other_family_component.head:
                    other_family_head = other_family_component.head
                    other_family_head.get_component(Character).influence_points -= 50
                    self.add_reaction(
                        IncrementOpinion(other_family_head, self.character, -10)
                    )
                    self.character.get_component(Character).influence_points += 50

        ExtortLocalFamiliesEvent(self.character).log_event()


class QuellRevoltAction(AIAction):
    """A parameterized instance of a quell revolt action."""

    __action_cost__ = 0
    __action_cooldown__ = 2

    __slots__ = ("character", "territory")

    character: Entity
    territory: Entity

    def __init__(self, character: Entity, territory: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.territory = territory
        self.context["territory"] = territory

    def on_execute(self) -> None:

        config = self.world.get_resource(Config)

        self.territory.remove_component(InRevolt)

        performer_character_comp = self.initiator.get_component(Character)
        if performer_character_comp.family:
            increment_prestige_base(performer_character_comp.family, 1)

        set_happiness_base(self.territory, config.base_territory_happiness)

        self.initiator.get_component(CharacterMetrics).data.num_revolts_quelled += 1

        QuellRevoltEvent(self.character, self.territory).log_event()


class TaxTerritoriesAction(AIAction):
    """An a family taxes their controlled territories for influence points."""

    __action_cost__ = 0
    __action_cooldown__ = 3

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character)
        self.character = character

    def on_execute(self) -> None:

        character_component = self.character.get_component(Character)
        family_head_component = self.initiator.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        for territory in family_component.controlled_territories:
            character_component.influence_points += 100
            increment_happiness_base(territory, -20)

        TaxTerritoriesEvent(self.character).log_event()


class StartWarSchemeAction(AIAction):
    """Action instance data for starting a war scheme against a specific person."""

    __action_cooldown__ = 3
    __action_cost__ = 0
    __action_tags__ = ["war", "power"]

    __slots__ = ("character", "target", "territory")

    character: Entity
    target: Entity
    territory: Entity

    def __init__(self, character: Entity, target: Entity, territory: Entity) -> None:
        super().__init__(character)
        self.territory = territory
        self.target = target
        self.character = character
        self.context["character"] = character
        self.context["target"] = target
        self.context["territory"] = territory

    def on_execute(self) -> None:

        scheme = create_war_scheme(
            initiator=self.initiator, target=self.target, territory=self.territory
        )

        self.character.get_component(SchemeManager).war_scheme = scheme

        StartWarSchemeEvent(self.character, self.target, self.territory).log_event()


class DeclareWarAction(AIAction):
    """The initiator declares war on the recipient for the target."""

    __action_tags__ = ["war", "power"]

    __slots__ = ("character", "opponent", "territory")

    def __init__(self, character: Entity, opponent: Entity, territory: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.opponent = opponent
        self.territory = territory
        self.context["opponent"] = opponent.name_with_uid
        self.context["territory"] = territory.name_with_uid

    def on_execute(self) -> None:

        DeclareWarEvent(self.character, self.opponent, self.territory).log_event()


class WinWarAction(AIAction):
    """The initiator wins a war (target) against the recipient."""

    __slots__ = ("character", "opponent", "territory")

    def __init__(self, character: Entity, opponent: Entity, territory: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.opponent = opponent
        self.territory = territory
        self.context["opponent"] = opponent.name_with_uid

    def on_execute(self) -> None:

        WarWonEvent(self.character, self.opponent, self.territory).log_event()


class StartCoupSchemeAction(AIAction):
    """Instance data for starting a scheme to overthrow the royal family."""

    __action_cost__ = 1000
    __action_cooldown__ = 5
    __action_tags__ = ["war", "deceit"]

    def __init__(self, character: Entity, target: Entity) -> None:
        super().__init__(character)
        self.target = target
        self.context["ruler"] = target.name_with_uid

    def on_execute(self) -> None:
        create_coup_scheme(initiator=self.initiator, target=self.target)

        self.initiator.get_component(CharacterMetrics).data.num_coups_planned += 1

        StartCoupSchemeEvent(self.initiator, self.target).log_event()


class CreateAllianceAction(AIAction):
    """A family head creates alliances for other families to join."""

    __slots__ = ("founder", "founding_family", "members")

    founder: Entity
    founding_family: Entity
    members: list[AllianceSchemeMember]

    def __init__(
        self,
        founder: Entity,
        founding_family: Entity,
        members: list[AllianceSchemeMember],
    ) -> None:
        super().__init__(founder)
        self.founder = founder
        self.founding_family = founding_family
        self.members = members

    def on_execute(self) -> None:
        alliance = start_alliance(self.founder, self.founding_family)
        StartAllianceEvent(self.founder, alliance).log_event()
        for entry in self.members:
            self.add_reaction(
                JoinAllianceAction(entry.character, entry.family, alliance)
            )


class JoinAllianceAction(AIAction):
    """Join an existing alliance."""

    __action_cost__ = 200
    __action_cooldown__ = 1

    __slots__ = ("character", "family", "alliance")

    character: Entity
    family: Entity
    alliance: Entity

    def __init__(self, character: Entity, family: Entity, alliance: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.family = family
        self.alliance = alliance

    def on_execute(self) -> None:
        family = self.initiator.get_component(Character).family

        if family is None:
            raise RuntimeError(f"{self.initiator.name_with_uid} is missing a family.")

        add_family_to_alliance(alliance=self.alliance, family=family)
        JoinAllianceEvent(self.character, family, self.alliance).log_event()


class JoinCoupSchemeAction(AIAction):
    """A character joins someones coup scheme."""

    __action_cost__ = 500
    __action_cooldown__ = 1

    __slots__ = ("character", "scheme")

    character: Entity
    scheme: Entity

    def __init__(self, character: Entity, scheme: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.scheme = scheme

    def on_execute(self) -> None:
        coup_scheme = self.scheme.get_component(CoupScheme)

        coup_scheme.members.append(self.character)

        self.character.get_component(SchemeManager).coup_scheme = self.scheme

        scheme_initiator = coup_scheme.initiator
        JoinCoupSchemeEvent(self.character, self.scheme, scheme_initiator).log_event()


class JoinAllianceSchemeAction(AIAction):
    """A character joins someones alliance scheme."""

    __action_cooldown__ = 1

    __slots__ = ("character", "family", "scheme")

    character: Entity
    family: Entity
    scheme: Entity

    def __init__(self, character: Entity, family: Entity, scheme: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.family = family
        self.scheme = scheme

    def on_execute(self) -> None:
        alliance_scheme = self.scheme.get_component(AllianceScheme)

        alliance_scheme.members.append(
            AllianceSchemeMember(self.character, self.family)
        )

        self.character.get_component(SchemeManager).alliance_scheme = self.scheme

        # JoinAllianceSchemeEvent(
        #     self.character, self.scheme, alliance_scheme.initiator
        # ).log_event()


class StartAllianceSchemeAction(AIAction):
    """A character begins a scheme to start an alliance."""

    __action_cost__ = 300
    __action_cooldown__ = 2

    __slots__ = ("character", "family")

    def __init__(self, character: Entity, family: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.family = family

    def on_execute(self) -> None:

        scheme = self.world.entity(name=f"{self.character}'s Alliance Scheme")

        scheme.add_component(
            AllianceScheme(
                initiator=self.initiator,
                initiator_family=self.family,
                start_year=self.world.get_resource(GameState).year,
            )
        )

        self.initiator.get_component(SchemeManager).alliance_scheme = scheme


class LeaveAllianceAction(AIAction):
    """A family head removes their family from its current alliance."""

    __action_cost__ = 200
    __action_cooldown__ = 1

    __slots__ = ("character", "family", "alliance")

    def __init__(self, character: Entity, family: Entity, alliance: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.family = family
        self.alliance = alliance

    def on_execute(self) -> None:
        family_head_component = self.initiator.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        alliance_component = self.alliance.get_component(Alliance)

        for member_family in alliance_component.member_families:
            if member_family == family_component.entity:
                continue

            member_family_component = member_family.get_component(Family)

            if member_family_component.head is not None:
                self.add_reaction(
                    IncrementOpinion(member_family_component.head, self.initiator, -20)
                )

        remove_family_from_alliance(alliance=self.alliance, family=self.family)

        LeaveAllianceEvent(
            alliance=self.alliance, family=self.family, family_head=self.character
        ).log_event()


class SeizeTerritoryAction(AIAction):
    """."""

    __action_cooldown__ = 1
    __action_cost__ = 200

    __slots__ = ("character", "territory")

    def __init__(self, character: Entity, territory: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.territory = territory
        self.context["territory"] = self.territory

    def on_execute(self) -> None:

        family_head_component = self.character.get_component(HeadOfFamily)

        self.add_reaction(
            SetTerritoryControllingFamily(self.territory, family_head_component.family)
        )

        self.initiator.get_component(CharacterMetrics).data.num_territories_taken += 1

        SeizeTerritoryEvent(
            self.character, family_head_component.family, self.territory
        ).log_event()


class CheatOnSpouseAction(AIAction):
    """A character cheats on their spouse."""

    __action_cost__ = 100
    __action_cooldown__ = 4
    __action_tags__ = ["infidelity"]

    __slots__ = ("character", "spouse", "accomplice")

    def __init__(self, character: Entity, spouse: Entity, accomplice: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.spouse = spouse
        self.accomplice = accomplice
        self.context["accomplice"] = self.accomplice.name_with_uid
        self.context["spouse"] = self.spouse.name_with_uid

    def on_execute(self) -> None:
        CheatOnSpouseEvent(self.character, self.spouse, self.accomplice).log_event()


class TryCheatOnSpouseAction(AIAction):
    """A character starts a scheme to cheat on their spouse."""

    __action_cost__ = 0
    __action_cooldown__ = 4
    __action_tags__ = ["infidelity"]

    __slots__ = ("character", "spouse", "accomplice")

    def __init__(self, character: Entity, spouse: Entity, accomplice: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.spouse = spouse
        self.accomplice = accomplice
        self.context["accomplice"] = self.accomplice.name_with_uid

    def on_execute(self) -> None:
        rng = self.world.get_resource(random.Random)

        # Evaluate the accomplices willingness to participate in
        # this activity if they are married
        accomplice_character = self.accomplice.get_component(Character)
        if accomplice_character.spouse is not None:

            accomplice_cheating_action = TryCheatOnSpouseAction(
                self.accomplice,
                accomplice_character.spouse,
                self.initiator,
            )

            action_utility = get_proclivity_score(accomplice_cheating_action)

            if rng.random() < action_utility:
                # Have to create an instance of the cheating action for the
                # initiator
                self.add_reaction(
                    CheatOnSpouseAction(
                        self.initiator,
                        self.spouse,
                        self.accomplice,
                    )
                )

                self.add_reaction(
                    CheatOnSpouseAction(
                        self.accomplice, accomplice_character.spouse, self.initiator
                    )
                )

                self.add_reaction(SexAction(self.accomplice, self.initiator))

            else:
                self.add_reaction(
                    IncrementAttraction(self.initiator, self.accomplice, -10)
                )
                self.add_reaction(
                    IncrementAttraction(self.accomplice, self.initiator, -10)
                )
                self.add_reaction(
                    IncrementOpinion(self.accomplice, self.initiator, -15)
                )

        # The accomplice is not married and so this is only sex
        else:

            accomplice_sex_action = SexAction(
                self.accomplice,
                self.initiator,
            )

            action_utility = get_proclivity_score(accomplice_sex_action)

            if rng.random() < action_utility:
                # Have to create an instance of the cheating action for the
                # initiator
                self.add_reaction(
                    CheatOnSpouseAction(
                        self.initiator,
                        self.spouse,
                        self.accomplice,
                    )
                )

                self.add_reaction(accomplice_sex_action)

            else:
                # Lower the attraction between the characters
                self.add_reaction(
                    IncrementAttraction(self.initiator, self.accomplice, -10)
                )
                self.add_reaction(
                    IncrementAttraction(self.accomplice, self.initiator, -10)
                )
                self.add_reaction(
                    IncrementOpinion(self.accomplice, self.initiator, -20)
                )


class DiscoverCoupScheme(AIAction):
    """The initiator discovers the recipient's coup scheme."""

    __slots__ = ("character", "scheme")

    def __init__(self, character: Entity, scheme: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.scheme = scheme

    def on_execute(self) -> None:
        CoupSchemeDiscoveredEvent(
            self.character, self.scheme.get_component(CoupScheme).initiator
        ).log_event()


class SentenceToDeath(AIAction):
    """The initiator sentences the recipient to death."""

    __slots__ = ("character", "reason", "target")

    def __init__(self, character: Entity, target: Entity, reason: str = "") -> None:
        super().__init__(character)
        self.character = character
        self.target = target
        self.reason = reason
        self.context["reason"] = reason

    def on_execute(self) -> None:
        SentenceToDeathEvent(self.character, self.target, self.reason).log_event()
        DieAction(self.target, cause="Sentenced to death").execute()


class OverthrowRulerAction(AIAction):
    """Overthrow the current ruler."""

    __slots__ = ("character", "ruler")

    def __init__(self, character: Entity, ruler: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.ruler = ruler

    def on_execute(self) -> None:
        UsurpThroneEvent(self.character, self.ruler).log_event()


class GetPregnant(AIAction):
    """An initiator character impregnates the recipient."""

    __slots__ = ("character", "partner")

    def __init__(self, character: Entity, partner: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.partner = partner

    def on_execute(self) -> None:
        current_year = self.world.get_resource(GameState).year

        character_comp = self.character.get_component(Character)

        # Add pregnancy component to character
        self.character.add_component(
            Pregnancy(
                assumed_father=character_comp.spouse,
                actual_father=self.partner,
                conception_year=current_year,
                due_year=current_year + 1,
            )
        )

        increment_fertility_base(self.character, -25)


class GiveBirth(AIAction):
    """The initiator gives birth to the recipient."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character)
        self.character = character

    def on_execute(self) -> None:
        pregnancy = self.character.get_component(Pregnancy)

        father = pregnancy.actual_father

        baby = spawn_baby_from(
            mother=self.character,
            father=father,
        )

        character = self.character.get_component(Character)

        set_character_mother(baby, self.character)
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
        set_relation_child(character.entity, baby)

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

        character.entity.remove_component(Pregnancy)

        # Reduce the character's fertility according to their species
        increment_fertility_base(
            self.character, -character.species.fertility_cost_per_child
        )

        GiveBirthEvent(self.character, baby).log_event()


class SexAction(AIAction):
    """A character has sex with another.

    If the character is female and their partner is male, calculate
    the chance of getting pregnant.
    """

    __action_cost__ = 0
    __action_cooldown__ = 3
    __action_tags__ = ["romance", "sex"]

    __slots__ = ("character", "partner")

    def __init__(self, character: Entity, partner: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.partner = partner

    def on_execute(self) -> None:
        rng = self.world.get_resource(random.Random)

        initiating_character = self.character.get_component(Character)
        partner_character = self.partner.get_component(Character)

        if initiating_character.sex == Sex.FEMALE and partner_character.sex == Sex.MALE:
            # Calculate the probability of getting pregnant if not already

            if self.character.has_component(Pregnancy):
                return

            initiator_fertility = get_fertility(self.character)
            partner_fertility = get_fertility(self.partner)

            if initiator_fertility <= 0 or partner_fertility <= 0:
                return

            chance_have_child = (initiator_fertility + partner_fertility) / 2

            if rng.randint(0, 100) < chance_have_child:
                self.add_reaction(GetPregnant(self.character, self.partner))

        elif (
            partner_character.sex == Sex.FEMALE and initiating_character.sex == Sex.MALE
        ):
            # Calculate the probability of getting pregnant if not already

            if self.partner.has_component(Pregnancy):
                return

            initiator_fertility = get_fertility(self.character)
            partner_fertility = get_fertility(self.partner)

            if initiator_fertility <= 0 or partner_fertility <= 0:
                return

            chance_have_child = (initiator_fertility + partner_fertility) / 2

            if rng.randint(0, 100) < chance_have_child:
                self.add_reaction(GetPregnant(self.partner, self.character))


class ClaimThroneAction(AIAction):
    """A family head claims the throne and right to rule."""

    __action_cost__ = 800
    __action_cooldown__ = 5
    __action_tags__ = ["power", "greed", "succession"]

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character)
        self.character = character

    def on_execute(self) -> None:

        # Start a new dynasty with this person
        start_new_dynasty(self.character)

        # Give the ruler and their existing children the royal blood trait
        add_trait(self.character, "royal_blood")

        character_component = self.character.get_component(Character)
        for child in character_component.children:
            add_trait(child, "royal_blood")

        # Increase the prestige of their family
        family = character_component.family
        assert family
        increment_prestige_base(family, 20)


class GoIntoRevolt(GameAction):
    """A territory goes into revolt against its controlling family.

    The head of the controlling family then has to resolve the revolt on their next
    turn. If not, the family loses control of the territory.
    """

    __slots__ = ("territory", "family")

    def __init__(self, territory: Entity, family: Entity) -> None:
        super().__init__(territory.world)
        self.territory = territory
        self.family = family

    def on_execute(self) -> None:
        current_year = self.world.get_resource(GameState).year
        self.territory.add_component(InRevolt(start_year=current_year))
        RevoltEvent(self.territory, self.family).log_event()


class BecomeFamilyHead(AIAction):
    """A character becomes head of their family."""

    __slots__ = ("character", "family")

    def __init__(self, character: Entity, family: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.family = family

    def on_execute(self) -> None:
        set_family_head(self.family, self.character)
        BecomeFamilyHeadEvent(self.character, self.family).log_event()


class LoseControlOfTerritory(AIAction):
    """A family head loses control of their territory."""

    __slots__ = ("character", "family", "territory")

    def __init__(self, character: Entity, family: Entity, territory: Entity) -> None:
        super().__init__(character)
        self.character = character
        self.family = family
        self.territory = territory
        self.context["character"] = character.name_with_uid
        self.context["family"] = family.name_with_uid
        self.context["territory"] = territory.name_with_uid

    def on_execute(self) -> None:
        """Perform the self."""
        self.add_reaction(UnsetControllingFamily(self.territory))
        LoseControlOfTerritoryEvent(self.family, self.territory).log_event()

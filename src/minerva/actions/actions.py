"""Concrete Action implementations."""

from __future__ import annotations

import logging
import random

from minerva.actions.base_types import AIAction, Scheme, get_proclivity_score
from minerva.actions.scheme_helpers import add_member_to_scheme
from minerva.actions.scheme_types import AllianceScheme, CoupScheme
from minerva.characters.components import (
    Character,
    Family,
    HeadOfFamily,
    LifeStage,
    Pregnancy,
    Prestige,
    Sex,
)
from minerva.characters.helpers import (
    get_fertility,
    get_prestige,
    increment_fertility_base,
    merge_family_with,
    remove_character_from_play,
    remove_heir,
    set_character_alive,
    set_character_biological_father,
    set_character_birth_family,
    set_character_family,
    set_character_father,
    set_character_life_stage,
    set_character_mother,
    set_family_head,
    set_prestige_base,
    set_relation_child,
    set_relation_sibling,
    start_marriage,
    update_grandparent_relations,
)
from minerva.characters.metric_data import CharacterMetrics
from minerva.characters.succession_helpers import start_new_dynasty
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
from minerva.ecs import Active, Entity
from minerva.pcg.character import spawn_baby_from
from minerva.relationships.base_types import Opinion
from minerva.relationships.helpers import (
    get_relationship,
    increment_attraction_base,
    increment_opinion_base,
)
from minerva.traits.helpers import add_trait
from minerva.world_map.components import InRevolt, PopulationHappiness, Territory
from minerva.world_map.helpers import (
    get_happiness_base,
    increment_happiness_base,
    increment_political_influence,
    set_happiness_base,
    set_territory_controlling_family,
)

_logger = logging.getLogger(__name__)


class GiveBackToTerritoryAction(AIAction):
    """An instance of a get married action."""

    __slots__ = ("character", "family", "territory")

    def __init__(self, character: Entity, family: Entity, territory: Entity) -> None:
        super().__init__("GiveBackToTerritory", character, territory)
        self.character = character
        self.family = family
        self.territory = territory
        self.context["territory"] = territory.name_with_uid
        self.context["family"] = family.name_with_uid

    def execute(self) -> None:
        increment_political_influence(self.territory, self.family, 5)
        set_happiness_base(self.territory, get_happiness_base(self.territory) + 5)

        self.log_event(self.character)


class GrowPoliticalInfluenceAction(AIAction):
    """A family head grows their political influence in a territory."""

    __slots__ = ("character", "territory", "family")

    def __init__(self, character: Entity, family: Entity, territory: Entity) -> None:
        super().__init__("GrowPoliticalInfluence", character, territory)
        self.character = character
        self.territory = territory
        self.family = family
        self.context["family"] = family.name_with_uid
        self.context["territory"] = territory.name_with_uid

    def execute(self) -> None:
        increment_political_influence(self.territory, self.family, 15)
        self.log_event(self.character)


class GetMarriedAction(AIAction):
    """An instance of a get married action."""

    __slots__ = ("character", "spouse")

    def __init__(self, character: Entity, spouse: Entity) -> None:
        super().__init__("GetMarried", character, spouse)
        self.character = character
        self.spouse = spouse
        self.context["spouse"] = spouse.name_with_uid

    def execute(self) -> None:
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

        self.log_event(self.character, self.spouse)


class BecomeSeniorAction(AIAction):
    """Initiator becomes a senior."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__("BecomeSenior", character)
        self.character = character

    def execute(self) -> None:
        set_character_life_stage(self.character, LifeStage.SENIOR)
        self.log_event(self.character)


class BecomeAdultAction(AIAction):
    """Initiator becomes an adult."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__("BecomeAdult", character)
        self.character = character

    def execute(self) -> None:
        set_character_life_stage(self.character, LifeStage.ADULT)
        self.log_event(self.character)


class BecomeYoungAdultAction(AIAction):
    """Initiator becomes a young adult."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__("BecomeYoungAdult", character)
        self.character = character

    def execute(self) -> None:
        set_character_life_stage(self.character, LifeStage.YOUNG_ADULT)
        self.log_event(self.character)


class BecomeAdolescentAction(AIAction):
    """Initiator becomes an adolescent."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__("BecomeAdolescent", character)
        self.character = character

    def execute(self) -> None:
        set_character_life_stage(self.character, LifeStage.ADOLESCENT)
        self.log_event(self.character)


class BecomeChildAction(AIAction):
    """Initiator becomes a child."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__("BecomeChild", character)
        self.character = character

    def execute(self) -> None:
        set_character_life_stage(self.character, LifeStage.CHILD)
        self.log_event(self.character)


class DieAction(AIAction):
    """Instance of an action where a character dies."""

    __slots__ = ("character", "cause")

    def __init__(self, character: Entity, cause: str = "") -> None:
        super().__init__("Die", character)
        self.character = character
        self.cause = cause
        self.context["cause"] = cause

    def execute(self) -> None:
        """Have a character die."""
        set_character_alive(self.character, False)

        self.character.deactivate()

        remove_character_from_play(self.character)

        self.log_event(self.character)


class SendGiftAction(AIAction):
    """One family head sends a gift to another."""

    __slots__ = ("character",)

    def __init__(self, character: Entity, recipient: Entity) -> None:
        super().__init__("SendGift", character, recipient)
        self.character = character
        self.recipient = recipient

    def execute(self) -> None:
        assert self.recipient

        get_relationship(self.recipient, self.character).get_component(
            Opinion
        ).base_value += 10

        self.log_event()


class SendAidAction(AIAction):
    """One family head sends a aid to another during a revolt."""

    __slots__ = ("character",)

    def __init__(self, character: Entity, recipient: Entity) -> None:
        super().__init__("SendAid", character, recipient)
        self.character = character
        self.recipient = recipient

    def execute(self) -> None:
        assert self.recipient

        performer_character_comp = self.character.get_component(Character)

        if performer_character_comp.family:
            performer_character_comp.family.get_component(Prestige).base_value += 10

        self.recipient.get_component(Character).influence_points += 50

        increment_opinion_base(get_relationship(self.recipient, self.character), 20)

        self.log_event()


class ExtortTerritoryOwnersAction(AIAction):
    """Ruler extorts all the families that control territories."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__("ExtortTerritoryOwners", character)
        self.character = character

    def execute(self) -> None:
        for _, (territory, _) in self.world.query_components((Territory, Active)):
            if territory.controlling_family:
                family_component = territory.controlling_family.get_component(Family)
                if family_component.head:
                    family_head = family_component.head
                    family_head.get_component(Character).influence_points -= 20
                    get_relationship(family_head, self.character).get_component(
                        Opinion
                    ).base_value -= 10

        self.log_event()


class ExtortLocalFamiliesAction(AIAction):
    """Family controlling a territory extorts other families residing there."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__("ExtortLocalFamilies", character)
        self.character = character

    def execute(self) -> None:
        current_date = self.world.get_resource(SimDate).year
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
                    other_family_head.get_component(Character).influence_points -= 5
                    get_relationship(other_family_head, self.character).get_component(
                        Opinion
                    ).base_value -= 10
                    self.character.get_component(Character).influence_points += 5

        _logger.info(
            "[%04d]: %s extorted the families in their territories.",
            current_date,
            self.character.name_with_uid,
        )


class QuellRevoltAction(AIAction):
    """A parameterized instance of a quell revolt action."""

    __slots__ = ("character", "territory")

    def __init__(self, character: Entity, territory: Entity) -> None:
        super().__init__("QuellRevolt", character, territory)
        self.territory = territory
        self.context["territory"] = territory.name_with_uid

    def execute(self) -> None:
        config = self.world.get_resource(Config)

        self.territory.remove_component(InRevolt)

        performer_character_comp = self.initiator.get_component(Character)
        if performer_character_comp.family:
            performer_character_comp.family.get_component(Prestige).base_value += 10

        population_happiness = self.territory.get_component(PopulationHappiness)

        population_happiness.base_value = config.base_territory_happiness

        self.initiator.get_component(CharacterMetrics).data.num_revolts_quelled += 1

        self.log_event(self.initiator)


class RevoltAgainstControllingFamily(AIAction):
    """The initiator(territory) starts a revolt against the recipient."""

    __slots__ = ("territory", "character")

    def __init__(self, territory: Entity, character: Entity) -> None:
        super().__init__("Revolt", territory, character)
        self.territory = territory
        self.character = character

    def execute(self) -> None:
        return


class TaxTerritoriesAction(AIAction):
    """An instance of a get married action."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__("TaxTerritories", character)
        self.character = character

    def execute(self) -> None:
        character_component = self.character.get_component(Character)
        character_component.influence_points += 250

        family_head_component = self.initiator.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        for territory in family_component.controlled_territories:
            increment_happiness_base(territory, -20)

        self.log_event(self.initiator)


class StartWarSchemeAction(AIAction):
    """Action instance data for starting a war scheme against a specific person."""

    __slots__ = ("character", "territory")

    def __init__(self, character: Entity, target: Entity, territory: Entity) -> None:
        super().__init__("StartWarScheme", character, target=target)
        self.territory = territory
        self.character = character
        self.context["character"] = character.name_with_uid
        self.context["territory"] = territory.name_with_uid

    def execute(self) -> None:
        assert self.target

        create_war_scheme(
            initiator=self.initiator, target=self.target, territory=self.territory
        )

        self.log_event()


class DeclareWar(AIAction):
    """The initiator declares war on the recipient for the target."""

    __slots__ = ("character", "opponent", "territory")

    def __init__(self, character: Entity, opponent: Entity, territory: Entity) -> None:
        super().__init__("DeclareWar", character, opponent, territory)
        self.character = character
        self.opponent = opponent
        self.territory = territory
        self.context["opponent"] = opponent.name_with_uid
        self.context["territory"] = territory.name_with_uid

    def execute(self) -> None:
        self.log_event(self.character, self.opponent)


class WinWarAction(AIAction):
    """The initiator wins a war (target) against the recipient."""

    __slots__ = ("character", "opponent")

    def __init__(self, character: Entity, opponent: Entity) -> None:
        super().__init__("WinWar", character, opponent)
        self.character = character
        self.opponent = opponent
        self.context["opponent"] = opponent.name_with_uid

    def execute(self) -> None:
        self.log_event(self.character, self.opponent)


class StartCoupSchemeAction(AIAction):
    """Instance data for starting a scheme to overthrow the royal family."""

    def __init__(self, character: Entity, target: Entity) -> None:
        super().__init__("StartCoupScheme", character, target=target)
        self.context["ruler"] = target.name_with_uid

    def execute(self) -> None:
        assert self.target

        create_coup_scheme(initiator=self.initiator, target=self.target)

        self.initiator.get_component(CharacterMetrics).data.num_coups_planned += 1

        self.log_event(self.initiator)


class CreateAllianceAction(AIAction):
    """A family head creates alliances for other families to join."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__("CreateAlliance", character)
        self.character = character

    def execute(self) -> None:
        self.log_event(self.character)


class JoinAllianceAction(AIAction):
    """Join an existing alliance."""

    __slots__ = ("character", "alliance")

    def __init__(self, character: Entity, alliance: Entity) -> None:
        super().__init__("JoinAlliance", character, alliance)
        self.character = character
        self.alliance = alliance

    def execute(self) -> None:
        family = self.initiator.get_component(Character).family

        if family is None:
            raise RuntimeError(f"{self.initiator.name_with_uid} is missing a family.")

        join_alliance(alliance=self.alliance, family=family)

        self.log_event(self.character)


class JoinCoupSchemeAction(AIAction):
    """A character joins someones coup scheme."""

    __slots__ = ("character", "scheme")

    def __init__(self, character: Entity, scheme: CoupScheme) -> None:
        super().__init__("JoinCoupScheme", character)
        self.character = character
        self.scheme = scheme

    def execute(self) -> None:
        add_member_to_scheme(self.scheme.entity, self.initiator)

        self.log_event(self.character)


class JoinAllianceSchemeAction(AIAction):
    """A character joins someones alliance scheme."""

    __slots__ = ("character", "scheme")

    def __init__(self, character: Entity, scheme: AllianceScheme) -> None:
        super().__init__("JoinAllianceScheme", character)
        self.context["scheme"] = scheme.entity.name_with_uid
        self.context["scheme_initiator"] = scheme.entity.get_component(
            Scheme
        ).initiator.name_with_uid
        self.character = character
        self.scheme = scheme

    def execute(self) -> None:
        add_member_to_scheme(self.scheme.entity, self.initiator)

        self.log_event(self.character)


class StartAllianceSchemeAction(AIAction):
    """Action instance data for starting a war scheme against a specific person."""

    def __init__(self, character: Entity) -> None:
        super().__init__("StartAllianceScheme", character)

    def execute(self) -> None:
        create_alliance_scheme(self.initiator)

        self.log_event(self.initiator)


class LeaveDisbandedAllianceAction(AIAction):
    """Leave an alliance that is disbanded."""

    def __init__(self, character: Entity) -> None:
        super().__init__("LeaveDisbandedAlliance", character)

    def execute(self) -> None:
        self.log_event(self.initiator)


class LeaveAllianceAction(AIAction):
    """Leave an alliance."""

    __slots__ = ("character", "alliance")

    def __init__(self, character: Entity, alliance: Entity) -> None:
        super().__init__("LeaveAlliance", character, alliance)
        self.character = character
        self.alliance = alliance

    def execute(self) -> None:
        family_head_component = self.initiator.get_component(HeadOfFamily)
        family_component = family_head_component.family.get_component(Family)

        alliance_component = self.alliance.get_component(Alliance)

        for member_family in alliance_component.member_families:
            if member_family == family_component.entity:
                continue

            member_family_component = member_family.get_component(Family)

            if member_family_component.head is not None:
                # LeftDisbandedAllianceEvent(
                #     subject=member_family_component.head,
                #     alliance=self.alliance,
                # ).log_event()

                get_relationship(
                    member_family_component.head, self.initiator
                ).get_component(Opinion).base_value -= 20

        end_alliance(self.alliance)

        self.initiator.get_component(CharacterMetrics).data.num_alliances_disbanded += 1

        # DisbandedAllianceEvent(
        #     subject=self.initiator, alliance=self.alliance
        # ).log_event()


class ExpandIntoTerritoryAction(AIAction):
    """."""

    __slots__ = ("territory",)

    def __init__(self, character: Entity, territory: Entity) -> None:
        super().__init__("ExpandIntoTerritory", character, territory)
        self.territory = territory
        self.context["territory"] = territory.name_with_uid

    def execute(self) -> None:
        family_head_component = self.initiator.get_component(HeadOfFamily)

        territory_component = self.territory.get_component(Territory)
        territory_component.political_influence[family_head_component.family] = 50
        family_head_component.family.get_component(Family).territories_present_in.add(
            self.territory
        )

        self.log_event(self.initiator)


class SeizeTerritoryAction(AIAction):
    """."""

    __slots__ = ("character", "territory")

    def __init__(self, character: Entity, territory: Entity) -> None:
        super().__init__("SeizeTerritory", character, territory)
        self.character = character
        self.territory = territory
        self.context["territory"] = self.territory.name_with_uid

    def execute(self) -> None:

        family_head_component = self.character.get_component(HeadOfFamily)

        set_territory_controlling_family(self.territory, family_head_component.family)

        self.initiator.get_component(CharacterMetrics).data.num_territories_taken += 1

        self.log_event(self.character)


class CheatOnSpouseAction(AIAction):
    """A character cheats on their spouse."""

    __slots__ = ("character", "spouse", "accomplice")

    def __init__(self, character: Entity, spouse: Entity, accomplice: Entity) -> None:
        super().__init__("CheatOnSpouse", character, spouse)
        self.character = character
        self.spouse = spouse
        self.accomplice = accomplice
        self.context["accomplice"] = self.accomplice.name_with_uid

    def execute(self) -> None:
        self.log_event(self.character)


class TryCheatOnSpouseAction(AIAction):
    """A character starts a scheme to cheat on their spouse."""

    __slots__ = ("character", "spouse", "accomplice")

    def __init__(self, character: Entity, spouse: Entity, accomplice: Entity) -> None:
        super().__init__("TryCheatOnSpouse", character, spouse)
        self.character = character
        self.spouse = spouse
        self.accomplice = accomplice
        self.context["accomplice"] = self.accomplice.name_with_uid

    def execute(self) -> None:
        rng = self.world.get_resource(random.Random)

        # Evaluate the accomplices willingness to participate in
        # this activity if they are married
        accomplice_character = self.accomplice.get_component(Character)
        if accomplice_character.spouse is not None:

            self.log_event(self.character, self.spouse, self.accomplice)

            accomplice_cheating_action = TryCheatOnSpouseAction(
                self.accomplice,
                accomplice_character.spouse,
                self.initiator,
            )

            action_utility = get_proclivity_score(accomplice_cheating_action)

            if rng.random() < action_utility:
                # Have to create an instance of the cheating action for the
                # initiator
                CheatOnSpouseAction(
                    self.initiator,
                    self.spouse,
                    self.accomplice,
                ).execute()

                accomplice_cheating_action.execute()

            else:
                increment_attraction_base(
                    get_relationship(self.initiator, self.accomplice), -10
                )
                increment_attraction_base(
                    get_relationship(self.accomplice, self.initiator), -10
                )
                increment_opinion_base(
                    get_relationship(self.accomplice, self.initiator), -15
                )

        # The accomplice is not married and so this is only sex
        else:

            self.log_event(self.character, self.spouse, self.accomplice)

            accomplice_sex_action = SexAction(
                self.accomplice,
                self.initiator,
            )

            action_utility = get_proclivity_score(accomplice_sex_action)

            if rng.random() < action_utility:
                # Have to create an instance of the cheating action for the
                # initiator
                CheatOnSpouseAction(
                    self.initiator,
                    self.spouse,
                    self.accomplice,
                ).execute()

                accomplice_sex_action.execute()

            else:
                # Lower the attraction between the characters
                increment_attraction_base(
                    get_relationship(self.initiator, self.accomplice), -10
                )
                increment_attraction_base(
                    get_relationship(self.accomplice, self.initiator), -10
                )
                increment_opinion_base(
                    get_relationship(self.accomplice, self.initiator), -15
                )


class DiscoverCoupScheme(AIAction):
    """The initiator discovers the recipient's coup scheme."""

    __slots__ = ("character", "scheme")

    def __init__(self, character: Entity, scheme: CoupScheme) -> None:
        super().__init__("DiscoverCoupScheme", character)
        self.character = character
        self.scheme = scheme

    def execute(self) -> None:
        self.log_event(self.initiator)


class SentenceToDeath(AIAction):
    """The initiator sentences the recipient to death."""

    __slots__ = ("character", "reason")

    def __init__(self, character: Entity, target: Entity, reason: str = "") -> None:
        super().__init__("SentenceToDeath", character, target)
        self.character = character
        self.target = target
        self.reason = reason
        self.context["reason"] = reason

    def execute(self) -> None:
        assert self.target
        self.log_event(self.character, self.target)
        DieAction(self.target, cause=self.action_type.display_name).execute()


class OverthrowRulerAction(AIAction):
    """Overthrow the current ruler."""

    __slots__ = ("character", "ruler")

    def __init__(self, character: Entity, ruler: Entity) -> None:
        super().__init__("OverthrowRuler", character, ruler)
        self.character = character
        self.ruler = ruler

    def execute(self) -> None:
        self.log_event(self.character, self.ruler)


class GetPregnant(AIAction):
    """An initiator character impregnates the recipient."""

    __slots__ = ("character", "partner")

    def __init__(self, character: Entity, partner: Entity) -> None:
        super().__init__("GetPregnant", character)
        self.character = character
        self.partner = partner

    def execute(self) -> None:
        current_year = self.world.get_resource(SimDate).year

        character_comp = self.character.get_component(Character)

        # Add pregnancy component to character
        self.character.add_component(
            Pregnancy(
                assumed_father=character_comp.spouse,
                actual_father=self.partner,
                conception_date=current_year,
                due_date=current_year + 1,
            )
        )

        increment_fertility_base(self.character, -25)


class GiveBirth(AIAction):
    """The initiator gives birth to the recipient."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__("GiveBirth", character)
        self.character = character

    def execute(self) -> None:
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


class SexAction(AIAction):
    """A character has sex with another.

    If the character is female and their partner is male, calculate
    the chance of getting pregnant.
    """

    __slots__ = ("character", "partner")

    def __init__(self, character: Entity, partner: Entity) -> None:
        super().__init__("Sex", character, partner)
        self.character = character
        self.partner = partner

    def execute(self) -> None:
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
                GetPregnant(self.character, self.partner).execute()


class ClaimThroneAction(AIAction):
    """A family head claims the throne and right to rule."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__("ClaimThrone", character)
        self.character = character

    def execute(self) -> None:

        # Start a new dynasty with this person
        start_new_dynasty(self.initiator)

        # Give the ruler and their existing children the royal blood trait
        add_trait(self.initiator, "royal_blood")

        character_component = self.initiator.get_component(Character)
        for child in character_component.children:
            add_trait(child, "royal_blood")

        # Increase the prestige of their family
        family = character_component.family
        assert family
        set_prestige_base(family, get_prestige(family) + 20)


class GoIntoRevolt(AIAction):
    """A territory goes into revolt against its controlling family.

    The head of the controlling family then has to resolve the revolt on their next
    turn. If not, the family loses control of the territory.
    """

    __slots__ = ("territory", "family")

    def __init__(self, territory: Entity, family: Entity) -> None:
        super().__init__("Revolt", territory, family)
        self.territory = territory
        self.family = family
        self.context["family"] = family.name_with_uid
        self.context["territory"] = territory.name_with_uid

    def execute(self) -> None:
        current_year = self.world.get_resource(SimDate).year
        self.territory.add_component(InRevolt(start_date=current_year))
        self.log_event()


class BecomeFamilyHead(AIAction):
    """A character becomes head of their family."""

    __slots__ = ("character", "family")

    def __init__(self, character: Entity, family: Entity) -> None:
        super().__init__("BecomeFamilyHead", initiator=character, recipient=family)
        self.character = character
        self.family = family

    def execute(self) -> None:
        set_family_head(self.family, self.character)
        self.log_event(self.character)


class LoseControlOfTerritory(AIAction):
    """A family head loses control of their territory."""

    __slots__ = ("character", "family", "territory")

    def __init__(self, character: Entity, family: Entity, territory: Entity) -> None:
        super().__init__("LoseControlOfTerritory", character, territory)
        self.character = character
        self.family = family
        self.territory = territory
        self.context["character"] = character.name_with_uid
        self.context["family"] = family.name_with_uid
        self.context["territory"] = territory.name_with_uid

    def execute(self) -> None:
        set_territory_controlling_family(self.territory, None)
        self.log_event(self.character)

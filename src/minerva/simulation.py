"""Minerva Simulation."""

from __future__ import annotations

import random
import sqlite3
from typing import Optional

import minerva.systems
from minerva.actions import behaviors
from minerva.actions.actions import DieAction, handle_character_death
from minerva.actions.base_types import (
    ActionTypeDatabase,
    AIActionType,
    AIBehaviorLibrary,
    AIBrain,
    AIBrainDatabase,
    GlobalProclivities,
)
from minerva.actions.selection_strategies import MaxUtilActionSelectStrategy
from minerva.actions.sensors import (
    TerritoriesControlledByOppsSensor,
    TerritoriesInRevoltSensor,
    UnControlledTerritoriesSensor,
    UnexpandedTerritoriesSensor,
)
from minerva.characters.components import (
    DynastyTracker,
    LifeStage,
    Sex,
    SexualOrientation,
    Species,
    SpeciesLibrary,
)
from minerva.characters.helpers import (
    RemoveCharacterFromPlay,
    RemoveFamilyFromPlay,
    remove_character_from_play,
    remove_family_from_play,
)
from minerva.characters.war_data import WarRole
from minerva.config import Config
from minerva.ecs import Entity, World
from minerva.game_action import ActionSystem
from minerva.game_state import GameState
from minerva.pcg.character import (
    SpawnCharacter,
    SpawnFamily,
    generate_character,
    generate_family,
)
from minerva.pcg.text_gen import Tracery
from minerva.sim_db import SimDB
from minerva.traits.base_types import CharacterTraitDatabase


class Simulation:
    """A Minerva simulation instance."""

    __slots__ = ("world",)

    world: World

    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Parameters
        ----------
        config
            Configuration parameters for the simulation, by default None.
            Simulation will use a default configuration if no config is
            provided.
        """
        _config = config if config is not None else Config()
        self.world = World()
        self.world.add_resource(GameState())
        self.world.add_resource(_config)
        self.world.add_resource(random.Random(_config.seed))
        self.world.add_resource(SpeciesLibrary())
        self.world.add_resource(CharacterTraitDatabase())
        self.world.add_resource(AIBehaviorLibrary())
        self.world.add_resource(DynastyTracker())
        self.world.add_resource(ActionTypeDatabase())
        self.world.add_resource(Tracery(self.config.seed))
        self.world.add_resource(SimDB(_config.db_path))
        self.world.add_resource(AIBrainDatabase())
        self.world.add_resource(GlobalProclivities())
        self.world.add_resource(ActionSystem())

        self.initialize_brains()
        self.initialize_systems()
        self.initialize_database()
        self.initialize_actions()
        self.initialize_behaviors()
        self.initialize_species_types()
        self.initialize_game_action_performers()

    def initialize_game_action_performers(self) -> None:
        """Initialize performers for GameActions."""
        action_system = self.world.get_resource(ActionSystem)
        action_system.attach_performer(SpawnCharacter, generate_character)
        action_system.attach_performer(SpawnFamily, generate_family)
        action_system.attach_performer(DieAction, handle_character_death)
        action_system.attach_performer(
            RemoveCharacterFromPlay, remove_character_from_play
        )
        action_system.attach_performer(RemoveFamilyFromPlay, remove_family_from_play)

    def initialize_brains(self) -> None:
        """Initialize built-in brains."""
        self.world.get_resource(AIBrainDatabase).add_brain(
            AIBrain(
                name="cpu",
                sensors=[
                    TerritoriesInRevoltSensor(),
                    UnexpandedTerritoriesSensor(),
                    UnControlledTerritoriesSensor(),
                    TerritoriesControlledByOppsSensor(),
                ],
                action_selection_strategy=MaxUtilActionSelectStrategy(),
            )
        )

    def initialize_systems(self) -> None:
        """Initialize built-in systems."""

        self.world.add_system(minerva.systems.TimeSystem())
        self.world.add_system(minerva.systems.CharacterAgingSystem())
        self.world.add_system(minerva.systems.CharacterLifespanSystem())
        self.world.add_system(minerva.systems.FamilyHeadSuccessionSystem())
        self.world.add_system(minerva.systems.RulerSuccessionSystem())
        self.world.add_system(minerva.systems.EmptyFamilyCleanUpSystem())
        self.world.add_system(minerva.systems.CharacterBehaviorSystem())
        self.world.add_system(minerva.systems.FamilyRoleSystem())
        self.world.add_system(minerva.systems.TerritoryRevoltSystem())
        self.world.add_system(minerva.systems.RevoltUpdateSystem())
        self.world.add_system(minerva.systems.TerritoryRandomEventSystem())
        self.world.add_system(minerva.systems.InfluencePointGainSystem())
        self.world.add_system(minerva.systems.PlaceholderMarriageSystem())
        self.world.add_system(minerva.systems.PregnancyPlaceHolderSystem())
        self.world.add_system(minerva.systems.ChildBirthSystem())
        self.world.add_system(minerva.systems.TerritoryInfluencePointBoostSystem())
        self.world.add_system(minerva.systems.SchemeUpdateSystems())
        self.world.add_system(minerva.systems.AllianceSchemeUpdateSystem())
        self.world.add_system(minerva.systems.WarSchemeUpdateSystem())
        self.world.add_system(minerva.systems.CoupSchemeUpdateSystem())
        self.world.add_system(minerva.systems.WarUpdateSystem())
        self.world.add_system(minerva.systems.ActionCooldownSystem())
        self.world.add_system(minerva.systems.FamilyRefillSystem())
        self.world.add_system(minerva.systems.HeirDeclarationSystem())
        self.world.add_system(minerva.systems.OrphanAdoptionSystem())
        self.world.add_system(minerva.systems.MapGenerationSystem())

    def initialize_actions(self) -> None:
        """Initialize actions."""
        database = self.world.get_resource(ActionTypeDatabase)
        database.add_action(
            AIActionType(
                name="GiveBackToTerritory",
                display_name="Give Back To Territory",
                cost=100,
                cooldown=4,
                tags=["generosity"],
                description=(
                    "[initiator] gave back to the small folk of the "
                    "[recipient] territory."
                ),
            )
        )
        database.add_action(
            AIActionType(
                name="GrowPoliticalInfluence",
                cost=400,
                cooldown=4,
                display_name="GrowPoliticalInfluence",
                description=(
                    "[initiator] grew the political influence of the "
                    "[family] family in the "
                    "[territory] territory."
                ),
            )
        )
        database.add_action(
            AIActionType(
                name="GetMarried",
                cost=0,
                cooldown=0,
                display_name="Get Married",
                description=("[initiator] and [recipient] got married."),
            )
        )
        database.add_action(
            AIActionType(
                name="Die",
                cost=0,
                cooldown=0,
                display_name="Die",
                description="[initiator] died (cause: [cause]).",
            )
        )
        database.add_action(
            AIActionType(
                name="BecomeChild",
                display_name="Become Child",
                description="[initiator] became a child.",
            )
        )
        database.add_action(
            AIActionType(
                name="BecomeAdolescent",
                display_name="Become Adolescent",
                description="[initiator] became an adolescent.",
            )
        )
        database.add_action(
            AIActionType(
                name="BecomeYoungAdult",
                display_name="Become Young Adult",
                description="[initiator] became a young adult.",
            )
        )
        database.add_action(
            AIActionType(
                name="BecomeAdult",
                display_name="Become Adult",
                description="[initiator] became an adult.",
            )
        )
        database.add_action(
            AIActionType(
                name="BecomeSenior",
                display_name="Become Senior",
                description="[initiator] became a senior.",
            )
        )
        database.add_action(
            AIActionType(
                name="BecameFamilyHead",
                display_name="Became Family Head",
                description=("[initiator] became head of the [recipient] family."),
            )
        )
        database.add_action(
            AIActionType(
                name="ChildBirth",
                display_name="ChildBirth",
                description=("[initiator] gave birth to [recipient]."),
            )
        )
        database.add_action(
            AIActionType(
                name="SentenceToDeath",
                display_name="Sentenced to Death",
                description=(
                    "[initiator] sentenced [recipient] to death for [reason]."
                ),
            )
        )
        database.add_action(
            AIActionType(
                name="TryCheatOnSpouse",
                display_name="Try to Cheat on Spouse",
                cost=400,
                cooldown=4,
                description=(
                    "[initiator] is attempting to cheat on [spouse] with [accomplice]."
                ),
            )
        )
        database.add_action(
            AIActionType(
                name="CheatOnSpouse",
                display_name="Cheat on Spouse",
                description=("[initiator] cheated on [spouse] with [accomplice]."),
                cost=400,
                cooldown=4,
            )
        )
        database.add_action(
            AIActionType(
                name="Sex",
                display_name="Sex",
                description="[subject] had sex with [recipient].",
                cost=400,
                cooldown=3,
            )
        )
        database.add_action(
            AIActionType(
                name="LoseControlOfTerritory",
                display_name="Lose Control of Territory",
                description="[initiator] lost control of the [territory] territory.",
            )
        )
        database.add_action(
            AIActionType(
                name="DeclareWar",
                display_name="DeclareWar",
                description=(
                    "[initiator] declared war against [opponent] for the "
                    "[territory] territory."
                ),
            )
        )
        database.add_action(
            AIActionType(
                name="WarWon",
                display_name="WarWon",
                description=(
                    "[initiator] won their war against "
                    "[opponent] for the "
                    "[territory] territory."
                ),
            )
        )
        database.add_action(
            AIActionType(
                name="StartWarScheme",
                display_name="Start War Scheme",
                cooldown=3,
                cost=300,
                description=(
                    "[initiator] started a war scheme against "
                    "[target] for the "
                    "[territory] territory."
                ),
            )
        )
        database.add_action(
            AIActionType(
                name="StartCoupScheme",
                cost=7000,
                cooldown=480,
                display_name="Start Coup Scheme",
                description=("[initiator] started a new coup scheme against [ruler]."),
            )
        )
        database.add_action(
            AIActionType(
                name="OverthrowRuler",
                display_name="OverthrowRuler",
                description=("[initiator] overthrew [ruler] for the throne."),
            )
        )
        database.add_action(
            AIActionType(
                name="DiscoverCoupScheme",
                display_name="DiscoverCoupScheme",
                description=("[initiator] discovered [target]'s coup scheme."),
            )
        )
        database.add_action(
            AIActionType(
                name="QuellRevolt",
                cost=200,
                cooldown=2,
                display_name="QuellRevolt",
                description=(
                    "[initiator] quelled a revolt in the [territory] territory."
                ),
            )
        )
        database.add_action(
            AIActionType(
                name="GiveBirth",
                display_name="Give Birth",
                description="[initiator] gave birth to a child.",
            )
        )
        database.add_action(
            AIActionType(
                name="LeaveAlliance",
                cost=1000,
                cooldown=12,
                display_name="Leave Alliance",
                description=("[initiator] left their alliance."),
            )
        )
        database.add_action(
            AIActionType(
                name="SendGift",
                display_name="Send Gift",
                description=("[initiator] sent a gift to [recipient]."),
                cost=200,
                cooldown=4,
            )
        )
        database.add_action(
            AIActionType(
                name="SendAid",
                display_name="Send Aid",
                description="[initiator] sent aid to [recipient].",
                cost=100,
                cooldown=4,
            )
        )
        database.add_action(
            AIActionType(
                name="ExtortTerritoryOwners",
                display_name="Extort Territory Owners",
                description="[initiator] extorted the territory controllers.",
                cost=500,
                cooldown=4,
            )
        )
        database.add_action(
            AIActionType(
                name="ExtortLocalFamilies",
                display_name="Extort Local Families",
                description="[initiator] extorted the families in their territories.",
                cost=500,
                cooldown=4,
            )
        )
        database.add_action(
            AIActionType(
                name="GetPregnant",
                display_name="GetPregnant",
                description="[initiator] became pregnant.",
            )
        )
        database.add_action(
            AIActionType(
                name="ClaimThrone",
                cost=600,
                cooldown=6,
                display_name="Became Ruler",
                description="[initiator] became ruler.",
            )
        )
        database.add_action(
            AIActionType(
                name="TaxTerritories",
                cost=100,
                cooldown=3,
                display_name="TaxTerritories",
                description=("[initiator] taxed their territories."),
            )
        )
        database.add_action(
            AIActionType(
                name="JoinCoupScheme",
                cost=3000,
                cooldown=12,
                display_name="Join Coup Scheme",
                description=("[initiator] joined [coup_planner]'s coup scheme."),
            )
        )
        database.add_action(
            AIActionType(
                name="JoinAlliance",
                display_name="Join Alliance",
                description=("[initiator] joined an alliance."),
                cost=400,
                cooldown=4,
            )
        )
        database.add_action(
            AIActionType(
                name="Revolt",
                display_name="Revolt",
                description=(
                    "The [territory] territory is revolting against the "
                    "[family] family."
                ),
            )
        )
        database.add_action(
            AIActionType(
                name="BecomeFamilyHead",
                display_name="Become Family Head",
                description=("[initiator] became head of their family."),
            )
        )
        database.add_action(
            AIActionType(
                name="JoinAllianceScheme",
                cost=0,
                cooldown=5,
                display_name="JoinAllianceScheme",
                description=(
                    "[initiator] joined [scheme_initiator]'s alliance scheme."
                ),
            )
        )
        database.add_action(
            AIActionType(
                name="CreateAlliance",
                cost=0,
                cooldown=0,
                display_name="Create Alliance",
                description=("[initiator] created a new alliance."),
            )
        )
        database.add_action(
            AIActionType(
                name="StartAllianceScheme",
                cost=500,
                cooldown=6,
                display_name="Attempting to Form An Alliance",
                description=("[initiator] is attempting to form a alliance."),
            )
        )
        database.add_action(
            AIActionType(
                name="ExpandIntoTerritory",
                cooldown=6,
                cost=500,
                display_name="Expanded Family Territory",
                description=(
                    "[initiator] started building influence in the "
                    "[territory] territory."
                ),
            )
        )
        database.add_action(
            AIActionType(
                name="SeizeTerritory",
                cooldown=3,
                cost=200,
                display_name="Take Over Territory",
                description=("[initiator] took control of the [territory] territory."),
            )
        )
        database.add_action(
            AIActionType(
                name="LeftDisbandedAlliance",
                display_name="Left Disbanded Alliance",
                description=("[initiator] left their alliance after it disbanded."),
            )
        )

    def initialize_behaviors(self) -> None:
        """Initialize behaviors."""
        database = self.world.get_resource(AIBehaviorLibrary)

        database.add_behavior(behaviors.SendGiftBehavior())
        database.add_behavior(behaviors.SendAidBehavior())
        database.add_behavior(behaviors.GiveToSmallFolkBehavior())
        database.add_behavior(behaviors.GrowPoliticalInfluenceBehavior())
        database.add_behavior(behaviors.ExtortTerritoryOwners())
        database.add_behavior(behaviors.ExtortLocalFamiliesBehavior())
        database.add_behavior(behaviors.QuellRevolt())
        database.add_behavior(behaviors.TaxTerritories())
        database.add_behavior(behaviors.ExpandPoliticalDomain())
        database.add_behavior(behaviors.SeizeControlOfTerritory())
        database.add_behavior(behaviors.StartAllianceSchemeBehavior())
        database.add_behavior(behaviors.JoinAllianceSchemeBehavior())
        database.add_behavior(behaviors.JoinExistingAlliance())
        database.add_behavior(behaviors.LeaveAlliance())
        database.add_behavior(behaviors.DeclareWarBehavior())
        database.add_behavior(behaviors.PlanCoupBehavior())
        database.add_behavior(behaviors.JoinCoupSchemeBehavior())
        database.add_behavior(behaviors.ClaimThroneBehavior())
        # database.add_behavior(behaviors.CheatOnSpouseBehavior())

    def initialize_species_types(self) -> None:
        """Initialize species types."""
        self.world.get_resource(SpeciesLibrary).add_species(
            Species(
                definition_id="human",
                name="Human",
                description="A plain ol' human being.",
                adolescent_age=13,
                young_adult_age=20,
                adult_age=40,
                senior_age=65,
                adolescent_male_fertility=100,
                young_adult_male_fertility=100,
                adult_male_fertility=100,
                senior_male_fertility=80,
                adolescent_female_fertility=100,
                young_adult_female_fertility=100,
                adult_female_fertility=0,
                senior_female_fertility=0,
                fertility_cost_per_child=20,
                lifespan=(70, 80),
                can_physically_age=True,
            )
        )

    def initialize_database(self) -> None:
        """Initialize the simulation database."""

        def adapt_entity(obj: Entity) -> int:
            return obj.uid

        def convert_entity(s: bytes):
            uid = int(str(s))

            return self.world.get_entity(uid)

        def adapt_sex(sex: Sex) -> str:
            return sex.name

        def convert_sex(s: bytes):
            return Sex(str(s))

        def adapt_life_stage(life_stage: LifeStage) -> str:
            return life_stage.name

        def convert_life_stage(s: bytes):
            return LifeStage(str(s))

        def adapt_sexual_orientation(orientation: SexualOrientation) -> str:
            return orientation.name

        def convert_sexual_orientation(s: bytes):
            return SexualOrientation(str(s))

        def adapt_war_role(war_role: WarRole) -> str:
            return war_role.name

        def convert_war_role(s: bytes):
            return WarRole(str(s))

        sqlite3.register_adapter(Entity, adapt_entity)
        sqlite3.register_converter("Entity", convert_entity)
        sqlite3.register_adapter(Sex, adapt_sex)
        sqlite3.register_converter("Sex", convert_sex)
        sqlite3.register_adapter(LifeStage, adapt_life_stage)
        sqlite3.register_converter("LifeStage", convert_life_stage)
        sqlite3.register_adapter(SexualOrientation, adapt_sexual_orientation)
        sqlite3.register_converter("SexualOrientation", convert_sexual_orientation)
        sqlite3.register_adapter(WarRole, adapt_war_role)
        sqlite3.register_converter("WarRole", convert_war_role)

    @property
    def config(self) -> Config:
        """Config parameters for the simulation."""
        return self.world.get_resource(Config)

    @property
    def game_state(self) -> GameState:
        """The current date in the simulation."""
        return self.world.get_resource(GameState)

    def step(self) -> None:
        """Advance the simulation by one timestep."""
        self.world.step()

    def export_db(self, export_path: str) -> None:
        """Export db to file on disk."""
        out = sqlite3.Connection(export_path)
        self.world.get_resource(SimDB).conn.backup(out)

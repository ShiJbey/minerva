"""Minerva Simulation."""

from __future__ import annotations

import random
import sqlite3
from typing import Optional

import minerva.systems
from minerva.actions import behaviors
from minerva.actions.actions import SeizeTerritoryAction
from minerva.actions.base_types import (
    P_ALWAYS,
    AIBehaviorLibrary,
    AIBrain,
    AIBrainDatabase,
    Proclivity,
    ProclivityDatabase,
)
from minerva.actions.selection_strategies import WeightedActionSelectStrategy
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
from minerva.characters.war_data import WarRole
from minerva.config import Config
from minerva.content import social_rules
from minerva.ecs import Entity, World
from minerva.events import (
    AllianceDisbandedEvent,
    BecameRulerEvent,
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
    GiveBirthEvent,
    GiveToTerritoriesEvent,
    GlobalEventHistory,
    JoinAllianceEvent,
    JoinCoupSchemeEvent,
    LeaveAllianceEvent,
    LoseControlOfTerritoryEvent,
    MarriageEvent,
    PregnancyEvent,
    SentenceToDeathEvent,
    StartAllianceEvent,
    StartCoupSchemeEvent,
    StartWarSchemeEvent,
    TakeControlOfTerritoryEvent,
    UsurpThroneEvent,
    WarLostEvent,
    WarWonEvent,
)
from minerva.game_action import ActionSystem
from minerva.game_state import GameState
from minerva.pcg.text_gen import Tracery
from minerva.relationships.base_types import (
    RelationshipManager,
    RelationshipModifierDatabase,
)
from minerva.relationships.helpers import RelationshipSystem
from minerva.sim_db import SimDB
from minerva.status.systems import StatusSystem
from minerva.traits.base_types import CharacterTraitDatabase, RelationshipTraitDatabase


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
        self.world.add_resource(Tracery(self.config.seed))
        self.world.add_resource(SimDB(_config.db_path))
        self.world.add_resource(AIBrainDatabase())
        self.world.add_resource(ActionSystem())
        self.world.add_resource(RelationshipManager())
        self.world.add_resource(RelationshipModifierDatabase())
        self.world.add_resource(ProclivityDatabase())
        self.world.add_resource(GlobalEventHistory())
        self.world.add_resource(RelationshipTraitDatabase())

        self.initialize_brains()
        self.initialize_systems()
        self.initialize_database()
        self.initialize_social_rules()
        self.initialize_behaviors()
        self.initialize_species_types()
        self.initialize_game_action_performers()
        self.configure_events()

    def initialize_game_action_performers(self) -> None:
        """Initialize performers for GameActions."""
        self.world.get_resource(ProclivityDatabase).add_proclivity(
            SeizeTerritoryAction, Proclivity(P_ALWAYS)
        )

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
                action_selection_strategy=WeightedActionSelectStrategy(),
            )
        )

    def initialize_systems(self) -> None:
        """Initialize built-in systems."""

        self.world.add_system(minerva.systems.TimeSystem())
        self.world.add_system(minerva.systems.CharacterAgingSystem())
        self.world.add_system(minerva.systems.CharacterDeathSystem())
        self.world.add_system(minerva.systems.FamilyHeadSuccessionSystem())
        self.world.add_system(minerva.systems.RulerSuccessionSystem())
        self.world.add_system(minerva.systems.EmptyFamilyCleanUpSystem())
        self.world.add_system(minerva.systems.CharacterBehaviorSystem())
        self.world.add_system(minerva.systems.FamilyRoleSystem())
        self.world.add_system(minerva.systems.TerritoryRevoltSystem())
        self.world.add_system(minerva.systems.RevoltUpdateSystem())
        self.world.add_system(minerva.systems.TerritoryRandomEventSystem())
        self.world.add_system(minerva.systems.InfluencePointGainSystem())
        self.world.add_system(minerva.systems.MarriageSystem())
        self.world.add_system(minerva.systems.PregnancySystem())
        self.world.add_system(minerva.systems.ChildBirthSystem())
        self.world.add_system(minerva.systems.TerritoryInfluencePointBoostSystem())
        self.world.add_system(minerva.systems.SchemeUpdateSystems())
        self.world.add_system(minerva.systems.AllianceSchemeUpdateSystem())
        self.world.add_system(minerva.systems.WarSchemeUpdateSystem())
        self.world.add_system(minerva.systems.CoupSchemeUpdateSystem())
        self.world.add_system(minerva.systems.WarUpdateSystem())
        self.world.add_system(minerva.systems.FamilyRefillSystem())
        self.world.add_system(minerva.systems.HeirDeclarationSystem())
        self.world.add_system(minerva.systems.OrphanAdoptionSystem())
        self.world.add_system(minerva.systems.MapGenerationSystem())
        self.world.add_system(RelationshipSystem())
        self.world.add_system(minerva.systems.AllianceSystem())
        self.world.add_system(StatusSystem())
        self.world.add_system(minerva.systems.GiftGivingSystem())
        self.world.add_system(minerva.systems.AidSendingSystem())
        self.world.add_system(minerva.systems.SeizeTerritoryControlSystem())

    def initialize_behaviors(self) -> None:
        """Initialize behaviors."""
        database = self.world.get_resource(AIBehaviorLibrary)

        database.add_behavior(behaviors.GiveBackToTerritoriesBehavior())
        database.add_behavior(behaviors.ExtortTerritoryOwners())
        database.add_behavior(behaviors.ExtortLocalFamiliesBehavior())
        database.add_behavior(behaviors.QuellRevolt())
        database.add_behavior(behaviors.TaxTerritories())
        database.add_behavior(behaviors.StartAllianceSchemeBehavior())
        database.add_behavior(behaviors.JoinAllianceSchemeBehavior())
        database.add_behavior(behaviors.JoinExistingAlliance())
        database.add_behavior(behaviors.LeaveAlliance())
        database.add_behavior(behaviors.DeclareWarBehavior())
        database.add_behavior(behaviors.PlanCoupBehavior())
        database.add_behavior(behaviors.JoinCoupSchemeBehavior())
        database.add_behavior(behaviors.ClaimThroneBehavior())
        # database.add_behavior(behaviors.CheatOnSpouseBehavior())

    def initialize_social_rules(self) -> None:
        """Initialize social rules"""
        social_rule_db = self.world.get_resource(RelationshipModifierDatabase)
        social_rule_db.add_attraction_modifiers(social_rules.ATTRACTION_RULES)
        social_rule_db.add_opinion_modifiers(social_rules.OPINION_RULES)

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

    def configure_events(self) -> None:
        """Configure simulation events."""

        BecomeFamilyHeadEvent.configure_db_table(self.world)
        DeathEvent.configure_db_table(self.world)
        BecomeSeniorEvent.configure_db_table(self.world)
        BecomeAdultEvent.configure_db_table(self.world)
        BecomeYoungAdultEvent.configure_db_table(self.world)
        BecomeAdolescentEvent.configure_db_table(self.world)
        BecomeChildEvent.configure_db_table(self.world)
        MarriageEvent.configure_db_table(self.world)
        PregnancyEvent.configure_db_table(self.world)
        GiveBirthEvent.configure_db_table(self.world)
        TakeControlOfTerritoryEvent.configure_db_table(self.world)
        LoseControlOfTerritoryEvent.configure_db_table(self.world)
        AllianceDisbandedEvent.configure_db_table(self.world)
        LeaveAllianceEvent.configure_db_table(self.world)
        JoinAllianceEvent.configure_db_table(self.world)
        GiveToTerritoriesEvent.configure_db_table(self.world)
        JoinCoupSchemeEvent.configure_db_table(self.world)
        StartCoupSchemeEvent.configure_db_table(self.world)
        StartWarSchemeEvent.configure_db_table(self.world)
        DeclareWarEvent.configure_db_table(self.world)
        WarLostEvent.configure_db_table(self.world)
        WarWonEvent.configure_db_table(self.world)
        StartAllianceEvent.configure_db_table(self.world)
        CoupSchemeDiscoveredEvent.configure_db_table(self.world)
        SentenceToDeathEvent.configure_db_table(self.world)
        UsurpThroneEvent.configure_db_table(self.world)
        CheatOnSpouseEvent.configure_db_table(self.world)
        BecameRulerEvent.configure_db_table(self.world)

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

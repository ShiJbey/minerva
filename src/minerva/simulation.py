"""Minerva Simulation."""

from __future__ import annotations

import logging
import pathlib
import random
import sqlite3
from typing import Optional

import minerva.actions.behaviors as behaviors
import minerva.systems
from minerva.actions.base_types import (
    AIActionLibrary,
    AIActionType,
    AIBehaviorLibrary,
    AIPreconditionGroup,
    AIUtilityConsiderationGroup,
    ConstantPrecondition,
    ConstantUtilityConsideration,
)
from minerva.actions.considerations import (
    AttractionToSpouse,
    AttractionToTarget,
    BoldnessConsideration,
    CompassionConsideration,
    DiplomacyConsideration,
    GreedConsideration,
    HonorConsideration,
    InfluencePointGoalConsideration,
    IntrigueConsideration,
    MartialConsideration,
    OpinionOfAllianceLeader,
    OpinionOfRecipientCons,
    OpinionOfRulerConsideration,
    OpinionOfSchemeInitiatorCons,
    OpinionOfSpouse,
    RationalityConsideration,
    StewardshipConsideration,
)
from minerva.actions.preconditions import (
    AreCoupSchemesActive,
    FamilyInAlliancePrecondition,
    HasActiveSchemes,
    IsAllianceMemberPlottingCoup,
    IsCurrentlyAtWar,
    IsFamilyHeadPrecondition,
    IsRulerPrecondition,
    JoinedAllianceScheme,
    Not,
)
from minerva.characters.components import (
    DynastyTracker,
    LifeStage,
    Sex,
    SexualOrientation,
    Species,
    SpeciesLibrary,
)
from minerva.characters.succession_helpers import SuccessionChartCache
from minerva.characters.war_data import WarRole
from minerva.config import Config
from minerva.datetime import SimDate
from minerva.ecs import Entity, World
from minerva.pcg.base_types import PCGFactories
from minerva.pcg.character import (
    DefaultBabyFactory,
    DefaultCharacterFactory,
    DefaultFamilyFactory,
)
from minerva.pcg.territory_pcg import DefaultTerritoryFactory
from minerva.pcg.text_gen import Tracery, TraceryNameFactory
from minerva.relationships import social_rules
from minerva.relationships.base_types import SocialRuleLibrary
from minerva.sim_db import DbTable, SimDB
from minerva.simulation_events import SimulationEvents
from minerva.traits.base_types import TraitLibrary


class Simulation:
    """A Minerva simulation instance."""

    __slots__ = "_config", "_world", "_date"

    _config: Config
    """Config parameters for the simulation."""
    _date: SimDate
    """The current date in the simulation."""
    _world: World
    """The simulation's ECS instance."""

    def __init__(self, config: Optional[Config] = None) -> None:
        """
        Parameters
        ----------
        config
            Configuration parameters for the simulation, by default None.
            Simulation will use a default configuration if no config is
            provided.
        """
        self._config = config if config is not None else Config()
        self._world = World()
        self._date = SimDate()

        # Seed the global rng for third-party packages
        random.seed(self._config.seed)

        self.initialize_resources()
        self.initialize_systems()
        self.initialize_logging()
        self.initialize_database()
        self.initialize_actions()
        self.initialize_behaviors()
        self.initialize_social_rules()
        self.initialize_species_types()

    def initialize_resources(self) -> None:
        """Initialize built-in resources."""

        self._world.add_resource(self._date)
        self._world.add_resource(self._config)
        self._world.add_resource(random.Random(self._config.seed))
        self._world.add_resource(
            PCGFactories(
                character_factory=DefaultCharacterFactory(
                    male_first_name_factory=TraceryNameFactory("#male_first_name#"),
                    female_first_name_factory=TraceryNameFactory("#female_first_name#"),
                    surname_factory=TraceryNameFactory("#surname#"),
                ),
                baby_factory=DefaultBabyFactory(),
                family_factory=DefaultFamilyFactory(
                    name_factory=TraceryNameFactory("#surname#")
                ),
                territory_factory=DefaultTerritoryFactory(
                    name_factory=TraceryNameFactory("#territory_name#")
                ),
            )
        )
        self._world.add_resource(SpeciesLibrary())
        self._world.add_resource(TraitLibrary())
        self._world.add_resource(SocialRuleLibrary())
        self._world.add_resource(SuccessionChartCache())
        self._world.add_resource(AIBehaviorLibrary())
        self._world.add_resource(DynastyTracker())
        self._world.add_resource(AIActionLibrary())
        self._world.add_resource(Tracery(self.config.seed))
        self._world.add_resource(SimulationEvents())
        self._world.add_resource(SimDB(self._config.db_path))

    def initialize_systems(self) -> None:
        """Initialize built-in systems."""

        self.world.add_system(
            minerva.systems.TickStatusEffectSystem(),
        )
        self.world.add_system(
            minerva.systems.TimeSystem(),
        )
        self.world.add_system(
            minerva.systems.CharacterAgingSystem(),
        )
        self.world.add_system(
            minerva.systems.SuccessionDepthChartUpdateSystem(),
        )
        self.world.add_system(
            minerva.systems.CharacterLifespanSystem(),
        )
        self.world.add_system(
            minerva.systems.FallbackFamilySuccessionSystem(),
        )
        self.world.add_system(
            minerva.systems.FallbackEmperorSuccessionSystem(),
        )
        self.world.add_system(
            minerva.systems.EmptyFamilyCleanUpSystem(),
        )
        self.world.add_system(
            minerva.systems.CharacterBehaviorSystem(),
        )
        self.world.add_system(
            minerva.systems.FamilyRoleSystem(),
        )
        self.world.add_system(
            minerva.systems.TerritoryRevoltSystem(),
        )
        self.world.add_system(
            minerva.systems.RevoltUpdateSystem(),
        )
        self.world.add_system(
            minerva.systems.TerritoryRandomEventSystem(),
        )
        self.world.add_system(
            minerva.systems.InfluencePointGainSystem(),
        )
        self.world.add_system(
            minerva.systems.PlaceholderMarriageSystem(),
        )
        self.world.add_system(
            minerva.systems.PregnancyPlaceHolderSystem(),
        )
        self.world.add_system(
            minerva.systems.ChildBirthSystem(),
        )
        self.world.add_system(
            minerva.systems.TerritoryInfluencePointBoostSystem(),
        )
        self.world.add_system(
            minerva.systems.SchemeUpdateSystems(),
        )
        self.world.add_system(
            minerva.systems.AllianceSchemeUpdateSystem(),
        )
        self.world.add_system(
            minerva.systems.WarSchemeUpdateSystem(),
        )
        self.world.add_system(
            minerva.systems.CoupSchemeUpdateSystem(),
        )
        self.world.add_system(
            minerva.systems.WarUpdateSystem(),
        )
        self.world.add_system(
            minerva.systems.ActionCooldownSystem(),
        )
        self.world.add_system(
            minerva.systems.FamilyRefillSystem(),
        )
        self.world.add_system(
            minerva.systems.HeirDeclarationSystem(),
        )
        self.world.add_system(
            minerva.systems.OrphanIdentificationSystem(),
        )
        self.world.add_system(
            minerva.systems.OrphanAdoptionSystem(),
        )
        self.world.add_system(
            minerva.systems.CheatSchemeUpdateSystem(),
        )
        self.world.add_system(minerva.systems.MapGenerationSystem())

    def initialize_actions(self) -> None:
        """Initialize actions."""
        action_library = self.world.get_resource(AIActionLibrary)

        action_library.add_action(
            AIActionType(
                name="Idle",
                cost=0,
                cooldown=0,
                utility_consideration=ConstantUtilityConsideration(0.4),
            )
        )

        action_library.add_action(
            AIActionType(
                name="SendGift",
                cost=200,
                cooldown=4,
                utility_consideration=AIUtilityConsiderationGroup(
                    DiplomacyConsideration(),
                    GreedConsideration().invert().pow(2),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="SendAid",
                cost=100,
                cooldown=4,
                utility_consideration=AIUtilityConsiderationGroup(
                    CompassionConsideration(),
                    GreedConsideration().invert().pow(2),
                    OpinionOfRecipientCons().pow(2),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="ExtortLocalFamilies",
                cost=500,
                cooldown=4,
                utility_consideration=AIUtilityConsiderationGroup(
                    GreedConsideration().pow(2),
                    BoldnessConsideration().pow(2),
                    CompassionConsideration().invert(),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="ExtortTerritoryOwners",
                cost=500,
                cooldown=4,
                utility_consideration=AIUtilityConsiderationGroup(
                    GreedConsideration().pow(2),
                    BoldnessConsideration().pow(2),
                    CompassionConsideration().invert(),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="Die",
                cost=0,
                cooldown=0,
                utility_consideration=ConstantUtilityConsideration(1.0),
            )
        )

        action_library.add_action(
            AIActionType(
                name="GetMarried",
                cost=0,
                cooldown=0,
                utility_consideration=ConstantUtilityConsideration(1.0),
            )
        )

        action_library.add_action(
            AIActionType(
                name="GiveBackToTerritory",
                cost=100,
                cooldown=4,
                utility_consideration=AIUtilityConsiderationGroup(
                    CompassionConsideration(),
                    GreedConsideration().invert(),
                    StewardshipConsideration(),
                    RationalityConsideration(),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="QuellRevolt",
                cost=200,
                cooldown=2,
                utility_consideration=AIUtilityConsiderationGroup(
                    ConstantUtilityConsideration(0.6),
                    StewardshipConsideration(),
                    RationalityConsideration(),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="GrowPoliticalInfluence",
                cost=400,
                cooldown=4,
                utility_consideration=AIUtilityConsiderationGroup(
                    GreedConsideration(),
                    BoldnessConsideration(),
                    DiplomacyConsideration(),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="SeizeTerritory",
                cooldown=3,
                cost=200,
                utility_consideration=AIUtilityConsiderationGroup(
                    ConstantUtilityConsideration(1.0),
                    AIUtilityConsiderationGroup(
                        GreedConsideration(),
                        BoldnessConsideration(),
                        op="max",
                    ),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="ExpandIntoTerritory",
                cooldown=6,
                cost=500,
                utility_consideration=AIUtilityConsiderationGroup(
                    ConstantUtilityConsideration(0.5),
                    BoldnessConsideration(),
                    AIUtilityConsiderationGroup(
                        GreedConsideration(),
                        MartialConsideration(),
                        op="max",
                    ),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="StartWarScheme",
                cooldown=3,
                cost=300,
                utility_consideration=AIUtilityConsiderationGroup(
                    BoldnessConsideration(),
                    ConstantUtilityConsideration(0.8),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="StartCoupScheme",
                cost=7000,
                cooldown=480,
                utility_consideration=AIUtilityConsiderationGroup(
                    HonorConsideration().invert().pow(2),
                    DiplomacyConsideration().invert().pow(2),
                    BoldnessConsideration().pow(2),
                    OpinionOfRulerConsideration().invert().pow(2),
                    IntrigueConsideration().pow(2),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="JoinCoupScheme",
                cost=3000,
                cooldown=12,
                utility_consideration=AIUtilityConsiderationGroup(
                    ConstantUtilityConsideration(0.3),
                    HonorConsideration().invert().pow(2),
                    IntrigueConsideration().pow(2),
                    BoldnessConsideration(),
                    OpinionOfRulerConsideration().invert(),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="JoinCoupScheme",
                cost=3000,
                cooldown=12,
                utility_consideration=AIUtilityConsiderationGroup(
                    ConstantUtilityConsideration(0.3),
                    HonorConsideration().invert().pow(2),
                    IntrigueConsideration().pow(2),
                    BoldnessConsideration(),
                    OpinionOfRulerConsideration().invert(),
                    OpinionOfSchemeInitiatorCons().pow(2),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="JoinAllianceScheme",
                cost=0,
                cooldown=5,
                utility_consideration=AIUtilityConsiderationGroup(
                    DiplomacyConsideration(),
                    OpinionOfSchemeInitiatorCons(),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="TaxTerritory",
                cost=100,
                cooldown=3,
                utility_consideration=AIUtilityConsiderationGroup(
                    GreedConsideration(),
                    CompassionConsideration().invert(),
                    InfluencePointGoalConsideration(400).invert(),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="StartAllianceScheme",
                cost=500,
                cooldown=6,
                utility_consideration=AIUtilityConsiderationGroup(
                    DiplomacyConsideration().pow(2),
                    StewardshipConsideration(),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="JoinAllianceScheme",
                cost=500,
                cooldown=4,
                utility_consideration=AIUtilityConsiderationGroup(
                    DiplomacyConsideration().pow(2),
                    StewardshipConsideration(),
                    OpinionOfSchemeInitiatorCons(),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="JoinExistingAlliance",
                cost=400,
                cooldown=4,
                utility_consideration=AIUtilityConsiderationGroup(
                    DiplomacyConsideration().pow(2),
                    StewardshipConsideration(),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="DisbandAlliance",
                cost=1000,
                cooldown=12,
                utility_consideration=AIUtilityConsiderationGroup(
                    DiplomacyConsideration().invert().pow(2),
                    HonorConsideration().invert(),
                    OpinionOfAllianceLeader().invert().pow(2),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="Sex",
                cost=400,
                cooldown=3,
                utility_consideration=AIUtilityConsiderationGroup(
                    AttractionToTarget("partner")
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="CheatOnSpouse",
                cost=400,
                cooldown=4,
                utility_consideration=AIUtilityConsiderationGroup(
                    HonorConsideration().invert().pow(2),
                    OpinionOfSpouse().invert().pow(2),
                    AttractionToSpouse().invert().pow(2),
                ),
            )
        )

        action_library.add_action(
            AIActionType(
                name="TryCheatOnSpouse",
                cost=400,
                cooldown=4,
                utility_consideration=AIUtilityConsiderationGroup(
                    HonorConsideration().invert().pow(2),
                    OpinionOfSpouse().invert().pow(2),
                    AttractionToSpouse().invert().pow(2),
                ),
            )
        )

    def initialize_behaviors(self) -> None:
        """Initialize behaviors."""
        behavior_library = self.world.get_resource(AIBehaviorLibrary)

        behavior_library.add_behavior(
            behaviors.IdleBehavior(
                name="Idle",
                precondition=ConstantPrecondition(True),
            )
        )

        behavior_library.add_behavior(
            behaviors.SendGiftBehavior(
                name="SendGift",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.SendAidBehavior(
                name="SendAid",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.GiveToSmallFolkBehavior(
                name="GiveToSmallfolk",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.GrowPoliticalInfluenceBehavior(
                name="GrowPoliticalInfluence",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.ExtortTerritoryOwners(
                name="ExtortTerritoryOwners",
                precondition=AIPreconditionGroup(
                    IsRulerPrecondition(),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.ExtortLocalFamiliesBehavior(
                name="ExtortLocalFamilies",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.QuellRevolt(
                name="QuellRevolt",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.TaxTerritory(
                name="TaxTerritory",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.ExpandPoliticalDomain(
                name="ExpandPoliticalDomain",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.SeizeControlOfTerritory(
                name="SeizeControlOfTerritory",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.StartAllianceSchemeBehavior(
                name="StartAllianceScheme",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.JoinAllianceSchemeBehavior(
                name="JoinAllianceScheme",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    Not(FamilyInAlliancePrecondition()),
                    Not(JoinedAllianceScheme()),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.JoinExistingAlliance(
                name="JoinExistingAlliance",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    Not(FamilyInAlliancePrecondition()),
                    Not(JoinedAllianceScheme()),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.DisbandAlliance(
                name="DisbandAlliance",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    FamilyInAlliancePrecondition(),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.DeclareWarBehavior(
                name="DeclareWar",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    Not(IsAllianceMemberPlottingCoup()),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.PlanCoupBehavior(
                name="PlanCoup",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    Not(IsRulerPrecondition()),
                    Not(IsAllianceMemberPlottingCoup()),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.JoinCoupSchemeBehavior(
                name="JoinCoupScheme",
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    Not(IsRulerPrecondition()),
                    AreCoupSchemesActive(),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.CheatOnSpouseBehavior(
                name="CheatOnSpouse",
                precondition=AIPreconditionGroup(ConstantPrecondition(True)),
            )
        )

    def initialize_social_rules(self) -> None:
        """Initialize social rules"""
        social_rule_library = self.world.get_resource(SocialRuleLibrary)

        social_rule_library.add_rule(social_rules.opinion_boost_for_family)
        social_rule_library.add_rule(social_rules.opinion_boost_for_birth_family)
        social_rule_library.add_rule(social_rules.not_attracted_to_parents)
        social_rule_library.add_rule(social_rules.opinion_boost_for_parents)
        social_rule_library.add_rule(social_rules.attraction_drop_for_children)
        social_rule_library.add_rule(social_rules.opinion_boost_for_children)
        social_rule_library.add_rule(social_rules.attraction_drop_for_siblings)
        social_rule_library.add_rule(social_rules.opinion_boost_for_siblings)
        social_rule_library.add_rule(social_rules.opinion_boost_for_spouse)
        social_rule_library.add_rule(social_rules.attraction_boost_for_spouse)

    def initialize_species_types(self) -> None:
        """Initialize species types."""
        species_library = self.world.get_resource(SpeciesLibrary)

        species_library.add_species(
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

    def initialize_logging(self) -> None:
        """Initialize simulation logging."""
        if self.config.logging_enabled:
            if self.config.log_to_terminal is False:
                # Output the logs to a file
                log_path = (
                    pathlib.Path(self.config.log_filepath)
                    if self.config.log_filepath
                    else pathlib.Path(f"./{self.config.seed}.minerva.log")
                )

                logging.basicConfig(
                    filename=log_path,
                    encoding="utf-8",
                    level=self.config.log_level,
                    format="%(message)s",
                    force=True,
                    filemode="w",
                )
            else:
                logging.basicConfig(
                    level=self.config.log_level,
                    format="%(message)s",
                    force=True,
                )

    def initialize_database(self) -> None:
        """Initialize the simulation database."""

        sim_db = self._world.get_resource(SimDB)

        sim_db.register_table(
            DbTable("relations")
            .with_int_column(
                "uid",
                is_primary_key=True,
                is_not_null=True,
            )
            .with_int_column(
                "character_id",
                is_not_null=True,
                foreign_key="characters.uid",
            )
            .with_int_column(
                "target_id",
                is_not_null=True,
                foreign_key="characters.uid",
            )
            .with_text_column("familial_relation")
            .with_text_column("relationship_status")
        )

        def adapt_gameobject(obj: Entity) -> int:
            return obj.uid

        def convert_gameobject(s: bytes):
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

        sqlite3.register_adapter(Entity, adapt_gameobject)
        sqlite3.register_converter("GameObject", convert_gameobject)
        sqlite3.register_adapter(Sex, adapt_sex)
        sqlite3.register_converter("Sex", convert_sex)
        sqlite3.register_adapter(LifeStage, adapt_life_stage)
        sqlite3.register_converter("LifeStage", convert_life_stage)
        sqlite3.register_adapter(SexualOrientation, adapt_sexual_orientation)
        sqlite3.register_converter("SexualOrientation", convert_sexual_orientation)
        sqlite3.register_adapter(WarRole, adapt_war_role)
        sqlite3.register_converter("WarRole", convert_war_role)

    @property
    def date(self) -> SimDate:
        """The current date in the simulation."""
        return self._date

    @property
    def world(self) -> World:
        """The simulation's ECS instance."""
        return self._world

    @property
    def config(self) -> Config:
        """Config parameters for the simulation."""
        return self._config

    def step(self) -> None:
        """Advance the simulation by one timestep."""
        self._world.step()

    def export_db(self, export_path: str) -> None:
        """Export db to file on disk."""
        out = sqlite3.Connection(export_path)
        self.world.get_resource(SimDB).db.backup(out)

    def dump_db_config_json(self) -> str:
        """Dumps the SQLite table configuration as a JSON string."""
        return self._world.get_resource(SimDB).dump_config_json()

    def dump_db_config_sql(self) -> str:
        """Dumps the SQLite table configurations as a SQLite config script."""
        return self._world.get_resource(SimDB).dump_config_sql()

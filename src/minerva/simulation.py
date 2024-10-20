"""Minerva Simulation."""

from __future__ import annotations

import logging
import pathlib
import random
import sqlite3
from typing import Optional

import minerva.actions.behaviors as behaviors
import minerva.systems
from minerva.actions.actions import DieActionType, GetMarriedActionType
from minerva.actions.base_types import (
    AIActionLibrary,
    AIBehaviorLibrary,
    AIConsiderationGroupOp,
    AIPreconditionGroup,
    AIUtilityConsiderationGroup,
    ConstantPrecondition,
    ConstantSuccessConsideration,
    ConstantUtilityConsideration,
)
from minerva.actions.behavior_helpers import (
    AreAlliancesActive,
    AreAllianceSchemesActive,
    AreCoupSchemesActive,
    BehaviorCostPrecondition,
    BoldnessConsideration,
    CompassionConsideration,
    DiplomacyConsideration,
    FamilyInAlliancePrecondition,
    GreedConsideration,
    HasActiveSchemes,
    HasTerritoriesInRevolt,
    HonorConsideration,
    InfluencePointConsideration,
    IntrigueConsideration,
    Invert,
    IsAllianceMemberPlottingCoup,
    IsCurrentlyAtWar,
    IsFamilyHeadPrecondition,
    IsRulerPrecondition,
    JoinedAllianceScheme,
    MartialConsideration,
    Not,
    OpinionOfAllianceLeader,
    OpinionOfRulerConsideration,
    RationalityConsideration,
    StewardshipConsideration,
    WantForPowerConsideration,
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
from minerva.config import Config
from minerva.datetime import SimDate
from minerva.ecs import GameObject, World
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
from minerva.sim_db import SimDB
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

        self._world.resources.add_resource(self._date)
        self._world.resources.add_resource(self._config)
        self._world.resources.add_resource(random.Random(self._config.seed))
        self._world.resources.add_resource(
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
        self._world.resources.add_resource(SpeciesLibrary())
        self._world.resources.add_resource(TraitLibrary())
        self._world.resources.add_resource(SocialRuleLibrary())
        self._world.resources.add_resource(SuccessionChartCache())
        self._world.resources.add_resource(AIBehaviorLibrary())
        self._world.resources.add_resource(DynastyTracker())
        self._world.resources.add_resource(AIActionLibrary())
        self._world.resources.add_resource(Tracery(self.config.seed))

    def initialize_systems(self) -> None:
        """Initialize built-in systems."""

        self.world.systems.add_system(
            minerva.systems.TickStatusEffectSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.TimeSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.CharacterAgingSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.SuccessionDepthChartUpdateSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.CharacterLifespanSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.FallbackFamilySuccessionSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.FallbackEmperorSuccessionSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.EmptyFamilyCleanUpSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.CharacterBehaviorSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.FamilyRoleSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.TerritoryRevoltSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.RevoltUpdateSystem(),
        )
        # self.world.systems.add_system(
        #     minerva.systems.TerritoryRandomEventSystem(),
        # )
        self.world.systems.add_system(
            minerva.systems.InfluencePointGainSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.PlaceholderMarriageSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.PregnancyPlaceHolderSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.ChildBirthSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.ProvinceInfluencePointBoostSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.SchemeUpdateSystems(),
        )
        self.world.systems.add_system(
            minerva.systems.AllianceSchemeUpdateSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.WarSchemeUpdateSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.CoupSchemeUpdateSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.WarUpdateSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.BehaviorCooldownSystem(),
        )

    def initialize_actions(self) -> None:
        """Initialize actions."""
        action_library = self.world.resources.get_resource(AIActionLibrary)

        action_library.add_action(
            DieActionType(
                success_consideration=ConstantSuccessConsideration(1.0),
                utility_consideration=ConstantUtilityConsideration(1.0),
                precondition=ConstantPrecondition(True),
            )
        )

        action_library.add_action(
            GetMarriedActionType(
                success_consideration=ConstantSuccessConsideration(1.0),
                utility_consideration=ConstantUtilityConsideration(1.0),
                precondition=ConstantPrecondition(False),
            )
        )

        action_library.add_action(
            behaviors.GiveBackToTerritoryActionType(
                success_consideration=ConstantSuccessConsideration(1.0),
                utility_consideration=ConstantUtilityConsideration(1.0),
                precondition=ConstantPrecondition(True),
            )
        )

        action_library.add_action(
            behaviors.QuellRevoltActionType(
                success_consideration=ConstantSuccessConsideration(1.0),
                utility_consideration=ConstantUtilityConsideration(1.0),
                precondition=ConstantPrecondition(True),
            )
        )

        action_library.add_action(
            behaviors.SeizeTerritoryActionType(
                success_consideration=ConstantSuccessConsideration(1.0),
                utility_consideration=ConstantUtilityConsideration(1.0),
                precondition=ConstantPrecondition(True),
            )
        )

        action_library.add_action(
            behaviors.ExpandIntoTerritoryActionType(
                success_consideration=ConstantSuccessConsideration(1.0),
                utility_consideration=ConstantUtilityConsideration(1.0),
                precondition=ConstantPrecondition(True),
            )
        )

        action_library.add_action(
            behaviors.StartWarSchemeActionType(
                success_consideration=ConstantSuccessConsideration(1.0),
                utility_consideration=ConstantUtilityConsideration(1.0),
                precondition=ConstantPrecondition(True),
            )
        )

        action_library.add_action(
            behaviors.TaxTerritoryActionType(
                success_consideration=ConstantSuccessConsideration(1.0),
                utility_consideration=ConstantUtilityConsideration(1.0),
                precondition=ConstantPrecondition(True),
            )
        )

    def initialize_behaviors(self) -> None:
        """Initialize behaviors."""
        behavior_library = self.world.resources.get_resource(AIBehaviorLibrary)

        behavior_library.add_behavior(
            behaviors.IdleBehavior(
                name="Idle",
                cooldown=0,
                cost=0,
                precondition=AIPreconditionGroup(
                    BehaviorCostPrecondition(),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.GiveToSmallfolkBehavior(
                name="GiveToSmallfolk",
                cooldown=2,
                cost=200,
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    BehaviorCostPrecondition(),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        Invert(GreedConsideration()),
                        CompassionConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.QuellRevolt(
                name="QuellRevolt",
                cooldown=2,
                cost=300,
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    BehaviorCostPrecondition(),
                    HasTerritoriesInRevolt(),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.MAX,
                    considerations=[
                        ConstantUtilityConsideration(0.6),
                        StewardshipConsideration(),
                        RationalityConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.TaxTerritory(
                name="TaxTerritory",
                cooldown=4,
                cost=50,
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    BehaviorCostPrecondition(),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.MAX,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        GreedConsideration(),
                        Invert(CompassionConsideration()),
                        Invert(InfluencePointConsideration(600)),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.ExpandPoliticalDomain(
                name="ExpandPoliticalDomain",
                cooldown=3,
                cost=500,
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    BehaviorCostPrecondition(),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        GreedConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.SeizeControlOfTerritory(
                name="SeizeControlOfTerritory",
                cooldown=3,
                cost=500,
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    BehaviorCostPrecondition(),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        GreedConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.FormAlliance(
                name="FormAlliance",
                cooldown=2,
                cost=500,
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    BehaviorCostPrecondition(),
                    Not(FamilyInAlliancePrecondition()),
                    Not(JoinedAllianceScheme()),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        DiplomacyConsideration(),
                        StewardshipConsideration(),
                        BoldnessConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.JoinAllianceScheme(
                name="JoinAllianceScheme",
                cooldown=0,
                cost=0,
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    BehaviorCostPrecondition(),
                    Not(FamilyInAlliancePrecondition()),
                    AreAllianceSchemesActive(),
                    Not(JoinedAllianceScheme()),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(1.0),
                        WantForPowerConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.JoinExistingAlliance(
                name="JoinExistingAlliance",
                cooldown=0,
                cost=300,
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    BehaviorCostPrecondition(),
                    Not(FamilyInAlliancePrecondition()),
                    AreAlliancesActive(),
                    Not(JoinedAllianceScheme()),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.4),
                        WantForPowerConsideration(),
                        DiplomacyConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.DisbandAlliance(
                name="DisbandAlliance",
                cooldown=0,
                cost=500,
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    BehaviorCostPrecondition(),
                    FamilyInAlliancePrecondition(),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        Invert(DiplomacyConsideration()),
                        Invert(OpinionOfAllianceLeader()),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.DeclareWar(
                name="DeclareWar",
                cooldown=3,
                cost=300,
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    BehaviorCostPrecondition(),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(1.0),
                        MartialConsideration(),
                        BoldnessConsideration(),
                        WantForPowerConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.PlanCoupBehavior(
                name="PlanCoup",
                cooldown=2,
                cost=2000,
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    BehaviorCostPrecondition(),
                    Not(IsRulerPrecondition()),
                    Not(IsAllianceMemberPlottingCoup()),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.2),
                        Invert(DiplomacyConsideration()),
                        Invert(HonorConsideration()),
                        BoldnessConsideration(),
                        WantForPowerConsideration(),
                        Invert(OpinionOfRulerConsideration()),
                        IntrigueConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.JoinCoupScheme(
                name="JoinCoupScheme",
                cooldown=2,
                cost=300,
                precondition=AIPreconditionGroup(
                    IsFamilyHeadPrecondition(),
                    BehaviorCostPrecondition(),
                    Not(IsRulerPrecondition()),
                    AreCoupSchemesActive(),
                    Not(HasActiveSchemes()),
                    Not(IsCurrentlyAtWar()),
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.3),
                        Invert(DiplomacyConsideration()),
                        Invert(HonorConsideration()),
                        BoldnessConsideration(),
                        WantForPowerConsideration(),
                        Invert(OpinionOfRulerConsideration()),
                    ],
                ),
            )
        )

    def initialize_social_rules(self) -> None:
        """Initialize social rules"""
        social_rule_library = self.world.resources.get_resource(SocialRuleLibrary)

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
        species_library = self.world.resources.get_resource(SpeciesLibrary)

        species_library.add_species(
            Species(
                definition_id="human",
                name="Human",
                description="A plain ol' human being.",
                adolescent_age=13,
                young_adult_age=20,
                adult_age=30,
                senior_age=65,
                adolescent_male_fertility=100,
                young_adult_male_fertility=100,
                adult_male_fertility=100,
                senior_male_fertility=80,
                adolescent_female_fertility=100,
                young_adult_female_fertility=100,
                adult_female_fertility=50,
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

        self._world.resources.add_resource(SimDB(self._config.db_path))

        def adapt_gameobject(obj: GameObject) -> int:
            return obj.uid

        def convert_gameobject(s: bytes):
            uid = int(str(s))

            return self.world.gameobjects.get_gameobject(uid)

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

        sqlite3.register_adapter(GameObject, adapt_gameobject)
        sqlite3.register_converter("GameObject", convert_gameobject)
        sqlite3.register_adapter(Sex, adapt_sex)
        sqlite3.register_converter("Sex", convert_sex)
        sqlite3.register_adapter(LifeStage, adapt_life_stage)
        sqlite3.register_converter("LifeStage", convert_life_stage)
        sqlite3.register_adapter(SexualOrientation, adapt_sexual_orientation)
        sqlite3.register_converter("SexualOrientation", convert_sexual_orientation)

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
        self.world.resources.get_resource(SimDB).db.backup(out)

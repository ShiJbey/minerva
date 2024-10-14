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
    BehaviorCostPrecondition,
    HasTerritoriesInRevolt,
    IsFamilyHeadPrecondition,
)
from minerva.businesses.data import BusinessLibrary, OccupationLibrary
from minerva.characters.components import (
    DynastyTracker,
    LifeStage,
    Sex,
    SexualOrientation,
    SpeciesLibrary,
)
from minerva.characters.motive_helpers import MotiveVector
from minerva.characters.succession_helpers import SuccessionChartCache
from minerva.config import Config
from minerva.datetime import SimDate
from minerva.ecs import GameObject, World
from minerva.effects.base_types import EffectLibrary
from minerva.effects.effects import (
    AddRelationshipModifierFactory,
    AddStatModifierFactory,
)
from minerva.pcg.character import CharacterNameFactory
from minerva.pcg.settlement import SettlementNameFactory
from minerva.preconditions.base_types import PreconditionLibrary
from minerva.preconditions.preconditions import (
    AreOppositeSexPreconditionFactory,
    AreSameSexPreconditionFactory,
    HasTraitPreconditionFactory,
    IsSexPreconditionFactory,
    LifeStageRequirementFactory,
    OwnerHasTraitPreconditionFactory,
    OwnerIsSexPreconditionFactory,
    OwnerLifeStageRequirementFactory,
    OwnerStatRequirementFactory,
    StatRequirementPreconditionFactory,
    TargetHasTraitPreconditionFactory,
    TargetIsSexPreconditionFactory,
    TargetLifeStageRequirementFactory,
    TargetStatRequirementFactory,
)
from minerva.relationships.base_types import SocialRuleLibrary
from minerva.sim_db import SimDB
from minerva.traits.base_types import Trait, TraitLibrary


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

    def initialize_resources(self) -> None:
        """Initialize built-in resources."""

        self._world.resources.add_resource(self._date)
        self._world.resources.add_resource(self._config)
        self._world.resources.add_resource(random.Random(self._config.seed))
        self._world.resources.add_resource(CharacterNameFactory(seed=self.config.seed))
        self._world.resources.add_resource(SettlementNameFactory(seed=self.config.seed))
        self._world.resources.add_resource(SpeciesLibrary())
        self._world.resources.add_resource(TraitLibrary())
        self._world.resources.add_resource(OccupationLibrary())
        self._world.resources.add_resource(BusinessLibrary())
        self._world.resources.add_resource(SocialRuleLibrary())
        self._world.resources.add_resource(SuccessionChartCache())
        self._world.resources.add_resource(AIBehaviorLibrary())
        self._world.resources.add_resource(DynastyTracker())
        self._world.resources.add_resource(AIActionLibrary())

        effect_lib = EffectLibrary()
        self._world.resources.add_resource(effect_lib)
        effect_lib.add_factory(AddStatModifierFactory())
        effect_lib.add_factory(AddRelationshipModifierFactory())

        precondition_lib = PreconditionLibrary()
        self._world.resources.add_resource(precondition_lib)
        precondition_lib.add_factory(HasTraitPreconditionFactory())
        precondition_lib.add_factory(OwnerHasTraitPreconditionFactory())
        precondition_lib.add_factory(TargetHasTraitPreconditionFactory())
        precondition_lib.add_factory(AreSameSexPreconditionFactory())
        precondition_lib.add_factory(AreOppositeSexPreconditionFactory())
        precondition_lib.add_factory(StatRequirementPreconditionFactory())
        precondition_lib.add_factory(OwnerStatRequirementFactory())
        precondition_lib.add_factory(TargetStatRequirementFactory())
        precondition_lib.add_factory(LifeStageRequirementFactory())
        precondition_lib.add_factory(OwnerLifeStageRequirementFactory())
        precondition_lib.add_factory(TargetLifeStageRequirementFactory())
        precondition_lib.add_factory(IsSexPreconditionFactory())
        precondition_lib.add_factory(OwnerIsSexPreconditionFactory())
        precondition_lib.add_factory(TargetIsSexPreconditionFactory())

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
            minerva.systems.SettlementRevoltSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.RevoltUpdateSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.SettlementRandomEventSystem(),
        )
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

        behavior_library = self.world.resources.get_resource(AIBehaviorLibrary)

        behavior_library.add_behavior(
            behaviors.IdleBehavior(
                motives=MotiveVector(),
                cost=0,
                precondition=AIPreconditionGroup(
                    [
                        BehaviorCostPrecondition(),
                    ]
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        # BehaviorMotiveConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.IncreasePoliticalPower(
                motives=MotiveVector(),
                cost=200,
                precondition=AIPreconditionGroup(
                    [
                        IsFamilyHeadPrecondition(),
                        BehaviorCostPrecondition(),
                    ]
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        # BehaviorMotiveConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.QuellRevolt(
                motives=MotiveVector(),
                cost=300,
                precondition=AIPreconditionGroup(
                    [
                        IsFamilyHeadPrecondition(),
                        BehaviorCostPrecondition(),
                        HasTerritoriesInRevolt(),
                    ]
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.MAX,
                    considerations=[
                        ConstantUtilityConsideration(0.6),
                        # BehaviorMotiveConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.TaxTerritory(
                motives=MotiveVector(),
                cost=50,
                precondition=AIPreconditionGroup(
                    [
                        IsFamilyHeadPrecondition(),
                        BehaviorCostPrecondition(),
                        HasTerritoriesInRevolt(),
                    ]
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.MAX,
                    considerations=[
                        ConstantUtilityConsideration(0.6),
                        # BehaviorMotiveConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.ExpandPoliticalDomain(
                motives=MotiveVector(),
                cost=500,
                precondition=AIPreconditionGroup(
                    [
                        IsFamilyHeadPrecondition(),
                        BehaviorCostPrecondition(),
                    ]
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        # BehaviorMotiveConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.SeizeControlOfTerritory(
                motives=MotiveVector(),
                cost=500,
                precondition=AIPreconditionGroup(
                    [
                        IsFamilyHeadPrecondition(),
                        BehaviorCostPrecondition(),
                    ]
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        # BehaviorMotiveConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.FormAlliance(
                motives=MotiveVector(),
                cost=500,
                precondition=AIPreconditionGroup(
                    [
                        IsFamilyHeadPrecondition(),
                        BehaviorCostPrecondition(),
                    ]
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        # BehaviorMotiveConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.JoinAllianceScheme(
                motives=MotiveVector(),
                cost=500,
                precondition=AIPreconditionGroup(
                    [
                        IsFamilyHeadPrecondition(),
                        BehaviorCostPrecondition(),
                    ]
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        # BehaviorMotiveConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.JoinExistingAlliance(
                motives=MotiveVector(),
                cost=500,
                precondition=AIPreconditionGroup(
                    [
                        IsFamilyHeadPrecondition(),
                        BehaviorCostPrecondition(),
                    ]
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        # BehaviorMotiveConsideration(),
                    ],
                ),
            )
        )

        behavior_library.add_behavior(
            behaviors.DisbandAlliance(
                motives=MotiveVector(),
                cost=500,
                precondition=AIPreconditionGroup(
                    [
                        IsFamilyHeadPrecondition(),
                        BehaviorCostPrecondition(),
                    ]
                ),
                utility_consideration=AIUtilityConsiderationGroup(
                    op=AIConsiderationGroupOp.GEOMETRIC_MEAN,
                    considerations=[
                        ConstantUtilityConsideration(0.5),
                        # BehaviorMotiveConsideration(),
                    ],
                ),
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

    def initialize_content(self) -> None:
        """Initialize game content from serialized data."""
        self._initialize_trait_data()
        self._world.initialize()

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

    def _initialize_trait_data(self) -> None:
        trait_library = self.world.resources.get_resource(TraitLibrary)
        effect_library = self.world.resources.get_resource(EffectLibrary)

        # Add the new definitions and instances to the library.
        for trait_def in trait_library.definitions.values():
            trait = Trait(
                trait_id=trait_def.trait_id,
                name=trait_def.name,
                inheritance_chance_both=trait_def.inheritance_chance_both,
                inheritance_chance_single=trait_def.inheritance_chance_single,
                is_inheritable=(
                    trait_def.inheritance_chance_single > 0
                    or trait_def.inheritance_chance_both > 0
                ),
                description=trait_def.description,
                effects=[
                    effect_library.create_from_obj(
                        self.world, {"reason": f"Has {trait_def.name} trait", **entry}
                    )
                    for entry in trait_def.effects
                ],
                tags=trait_def.tags.copy(),
                conflicting_traits=trait_def.conflicts_with,
            )

            trait_library.add_trait(trait)

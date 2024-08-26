"""Minerva Simulation."""

from __future__ import annotations

import logging
import pathlib
import random
import sqlite3
from typing import Optional

import minerva.systems
from minerva.businesses.data import BusinessLibrary, OccupationLibrary
from minerva.characters.components import (
    LifeStage,
    Sex,
    SexualOrientation,
    SpeciesLibrary,
)
from minerva.config import Config
from minerva.datetime import SimDate
from minerva.ecs import GameObject, World
from minerva.effects.base_types import EffectLibrary
from minerva.effects.effects import (
    AddRelationshipModifierFactory,
    AddStatModifierFactory,
)
from minerva.life_events.base_types import GlobalEventHistory
from minerva.pcg.character import CharacterNameFactory, ClanNameFactory
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

        self._init_resources()
        self._init_systems()
        self._init_logging()
        self._init_db()

    def _init_resources(self) -> None:
        """Initialize built-in resources."""

        self._world.resources.add_resource(self._date)
        self._world.resources.add_resource(self._config)
        self._world.resources.add_resource(random.Random(self._config.seed))
        self._world.resources.add_resource(CharacterNameFactory(seed=self.config.seed))
        self._world.resources.add_resource(SettlementNameFactory(seed=self.config.seed))
        self._world.resources.add_resource(ClanNameFactory(seed=self.config.seed))
        self._world.resources.add_resource(SpeciesLibrary())
        self._world.resources.add_resource(TraitLibrary())
        self._world.resources.add_resource(OccupationLibrary())
        self._world.resources.add_resource(BusinessLibrary())
        self._world.resources.add_resource(SocialRuleLibrary())
        self._world.resources.add_resource(GlobalEventHistory())

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

    def _init_systems(self) -> None:
        """Initialize built-in systems."""

        self.world.systems.add_system(
            minerva.systems.CompileTraitDefsSystem(),
        )
        # self.world.systems.add_system(CompileSpeciesDefsSystem())
        # self.world.systems.add_system(CompileJobRoleDefsSystem())
        # self.world.systems.add_system(CompileSkillDefsSystem())
        # self.world.systems.add_system(CompileDistrictDefsSystem())
        # self.world.systems.add_system(CompileSettlementDefsSystem())
        # self.world.systems.add_system(CompileCharacterDefsSystem())
        # self.world.systems.add_system(CompileBusinessDefsSystem())
        self.world.systems.add_system(
            minerva.systems.TickStatusEffectSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.TimeSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.InitializeWorldMap(),
        )
        self.world.systems.add_system(
            minerva.systems.InitializeClansSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.CharacterAgingSystem(),
        )
        self.world.systems.add_system(
            minerva.systems.CharacterLifespanSystem(),
        )

    def _init_logging(self) -> None:
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

    def _init_db(self) -> None:
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

    def initialize(self) -> None:
        """Run initialization systems only."""
        self._world.initialize()

    def step(self) -> None:
        """Advance the simulation by one timestep."""
        self._world.step()

    def export_db(self, export_path: str) -> None:
        """Export db to file on disk."""
        out = sqlite3.Connection(export_path)
        self.world.resources.get_resource(SimDB).db.backup(out)

"""Minerva Sample: House of the Dragon/Game of Thrones."""

import argparse
import logging
import pathlib
import pstats
import time
from cProfile import Profile
from datetime import datetime

import tqdm

from minerva.actions.base_types import AIBehavior, AIBehaviorLibrary
from minerva.characters.components import HeadOfClan
from minerva.characters.motive_helpers import MotiveVector
from minerva.config import Config
from minerva.datetime import MONTHS_PER_YEAR
from minerva.ecs import GameObject
from minerva.inspection import SimulationInspector
from minerva.loaders import (
    load_businesses_types,
    load_clan_names,
    load_female_first_names,
    load_male_first_names,
    load_occupation_types,
    load_settlement_names,
    load_species_types,
    load_surnames,
    load_traits,
)
from minerva.pcg.character import generate_initial_clans
from minerva.pcg.world_map import generate_world_map
from minerva.preconditions.preconditions import LambdaPrecondition
from minerva.simulation import Simulation

LOGGER = logging.getLogger(__file__)
DATA_DIR = pathlib.Path(__file__).parent.parent / "data"


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""

    parser = argparse.ArgumentParser(
        prog="Shogun Minerva Sample",
        description="Minerva simulation sample based on the Shogun board game.",
    )

    parser.add_argument(
        "-y", "--years", type=int, default=100, help="Number of years to simulate."
    )

    parser.add_argument(
        "--pygame", action="store_true", help="Run the PyGame visualization"
    )

    parser.add_argument(
        "--enable-logging", action="store_true", help="Enable simulation logging"
    )

    parser.add_argument(
        "--enable-profiling", action="store_true", help="Enable simulation profiling"
    )

    parser.add_argument(
        "--db-out",
        type=str,
        default=str(pathlib.Path(__file__).parent / "shogun.db"),
        help="The output location for the simulation database.",
    )

    return parser.parse_args()


def run_simulation_with_profiling(simulation: Simulation, years: int) -> None:
    """Run the simulation with profiling enabled."""

    total_time_steps: int = years * MONTHS_PER_YEAR

    with Profile() as profile:
        for _ in tqdm.trange(total_time_steps):  # type: ignore
            simulation.step()

        profile_path = "profile_{}_{}.prof".format(  # pylint: disable=C0209
            simulation.config.seed, datetime.now().strftime("%Y%m%d_%H_%M")
        )

        (
            pstats.Stats(profile)
            .strip_dirs()  # type: ignore
            .sort_stats(pstats.SortKey.PCALLS)
            .dump_stats(profile_path)
        )


def run_simulation(simulation: Simulation, years: int) -> None:
    """Runs the simulation."""
    total_time_steps: int = years * MONTHS_PER_YEAR

    for _ in tqdm.trange(total_time_steps):  # type: ignore
        simulation.step()


def run_visualization(simulation: Simulation) -> None:
    """Runs the simulation within a PyGame game."""
    # Import game below since PyGame requires addition loading time
    import minerva.constants  # pylint: disable=C0415
    from minerva.viz.game import Game  # pylint: disable=C0415

    minerva.constants.SHOW_DEBUG = True

    game = Game(simulation)
    game.run()


def add_simple_ai_behavior(simulation: Simulation) -> None:
    """Add a simple AI behavior to the simulation."""

    ai_behavior_library = simulation.world.resources.get_resource(AIBehaviorLibrary)

    def say_hi_behavior(character: GameObject) -> bool:
        LOGGER.info("%s says hi to the other leaders.", character.name_with_uid)
        return True

    ai_behavior_library.add_behavior(
        AIBehavior(
            name="Say Hi",
            motives=MotiveVector(happiness=1.0),
            preconditions=[
                LambdaPrecondition(
                    "Is clan head", lambda g: g.has_component(HeadOfClan)
                ),
            ],
            execution_strategy=say_hi_behavior,
        )
    )


if __name__ == "__main__":
    args = parse_args()

    sim = Simulation(
        Config(
            n_sovereign_clans=12,
            world_size=(25, 15),
            logging_enabled=bool(args.enable_logging),
            log_to_terminal=False,
        )
    )

    load_male_first_names(sim, DATA_DIR / "masculine_japanese_names.txt")
    load_female_first_names(sim, DATA_DIR / "feminine_japanese_names.txt")
    load_surnames(sim, DATA_DIR / "japanese_surnames.txt")
    load_settlement_names(sim, DATA_DIR / "japanese_city_names.txt")
    load_clan_names(sim, DATA_DIR / "japanese_surnames.txt")
    load_species_types(sim, DATA_DIR / "species_types.yaml")
    load_traits(sim, DATA_DIR / "ck3_traits.yaml")
    load_businesses_types(sim, DATA_DIR / "ds_business_types.yaml")
    load_occupation_types(sim, DATA_DIR / "ds_occupation_types.yaml")

    add_simple_ai_behavior(sim)

    print(f"World Seed: {sim.config.seed}")

    print("Initializing Data ...")
    sim.initialize_content()

    time.sleep(0.1)

    print("Generating Map and Territories ...")
    generate_world_map(sim.world)

    time.sleep(0.8)

    print("Generating Families ...")
    generate_initial_clans(sim.world)

    time.sleep(0.8)

    if args.enable_profiling:
        run_simulation_with_profiling(sim, int(args.years))
    elif args.pygame:
        run_visualization(sim)
    else:
        run_simulation(sim, int(args.years))

    sim.export_db(str(args.db_out))

    # Create inspector for when the script is run with the python "-i" flag
    inspector = SimulationInspector(sim)

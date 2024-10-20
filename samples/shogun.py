"""Minerva Sample: Shogun.

This minerva sample generates a world inspired by the Shogun board game, based on the
novel of the same name. This sample is the core testing script for the headless and
pygame version.

Usage:
    "python path/to/shogun.py -h".............Show commandline help
    "python path/to/shogun.py"................Run headless sim
    "python path/to/shogun.py --pygame".......Run the pygame visualization
"""

import argparse
import logging
import pathlib
import pstats
import random
import time
from cProfile import Profile
from datetime import datetime

import tqdm

import minerva
from minerva.config import Config
from minerva.data import ck3_traits, japanese_city_names, japanese_names
from minerva.datetime import MONTHS_PER_YEAR
from minerva.inspection import SimulationInspector
from minerva.pcg.character import generate_initial_families
from minerva.pcg.world_map import generate_world_map
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
        "-s",
        "--seed",
        type=str,
        default=str(random.randint(0, 999_999)),
        help="A world seed for random number generation.",
    )

    parser.add_argument(
        "-y", "--years", type=int, default=100, help="Number of years to simulate."
    )

    parser.add_argument(
        "--pygame", action="store_true", help="Run the PyGame visualization"
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug output")

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

    print(f"Simulating {years} years ({total_time_steps} timesteps) ...")

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

    print(f"Simulating {years} years ({total_time_steps} timesteps) ...")

    for _ in tqdm.trange(total_time_steps):  # type: ignore
        simulation.step()


def run_visualization(simulation: Simulation) -> None:
    """Runs the simulation within a PyGame game."""
    # Import game below since PyGame requires addition loading time
    from minerva.viz.game import Game  # pylint: disable=C0415

    game = Game(simulation)
    game.run()


if __name__ == "__main__":
    args = parse_args()

    sim = Simulation(
        Config(
            seed=args.seed,
            world_size=(25, 15),
            logging_enabled=bool(args.enable_logging),
            log_to_terminal=False,
            log_level="DEBUG" if args.debug else "INFO",
            show_debug=args.debug if args.debug else False,
        )
    )

    japanese_city_names.load_names(sim.world)
    japanese_names.load_names(sim.world)
    ck3_traits.load_traits(sim.world)

    print(f"Minerva version: {minerva.__version__}")
    print(f"World Seed: {sim.config.seed}")

    print("Generating Map and Territories ...")
    generate_world_map(sim.world)

    time.sleep(0.8)

    print("Generating Initial Families ...")
    generate_initial_families(sim.world)

    time.sleep(0.8)

    if bool(args.enable_profiling):
        run_simulation_with_profiling(sim, int(args.years))
    elif bool(args.pygame):
        run_visualization(sim)
    else:
        run_simulation(sim, int(args.years))

    sim.export_db(str(args.db_out))

    # Create inspector for when the script is run with the python "-i" flag
    inspector = SimulationInspector(sim)

    print("Done.")

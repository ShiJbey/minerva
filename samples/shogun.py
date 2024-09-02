"""Minerva Sample: House of the Dragon/Game of Thrones."""

import pathlib
import pstats
import time
from cProfile import Profile
from datetime import datetime
from pickle import TRUE

import tqdm

from minerva.config import Config
from minerva.datetime import MONTHS_PER_YEAR
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
from minerva.simulation import Simulation, generate_world_map

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
DB_OUTPUT_PATH = str(pathlib.Path(__file__).parent / "shogun.db")
YEARS = 10
ENABLE_PROFILING = False
USE_VIZ = True
LOGGING_ENABLED = False


def run_simulation_with_profiling(simulation: Simulation) -> None:
    """Run the simulation with profiling enabled."""
    print("Initializing Data ...")
    simulation.initialize_content()

    time.sleep(0.1)

    print("Generating Map and Territories ...")
    generate_world_map(simulation)

    time.sleep(0.8)

    print("Generating Families ...")

    time.sleep(0.8)

    total_time_steps: int = YEARS * MONTHS_PER_YEAR

    with Profile() as profile:
        for _ in tqdm.trange(total_time_steps):  # type: ignore
            simulation.step()

        profile_path = f"profile_{datetime.now().strftime('%Y%m%d_%H_%M')}.prof"

        (
            pstats.Stats(profile)
            .strip_dirs()  # type: ignore
            .sort_stats(pstats.SortKey.PCALLS)
            .dump_stats(profile_path)
        )


def run_simulation(simulation: Simulation) -> None:
    """Runs the simulation."""
    total_time_steps: int = YEARS * MONTHS_PER_YEAR

    print("Initializing Data ...")
    simulation.initialize_content()

    time.sleep(0.1)

    print("Generating Map and Territories ...")
    generate_world_map(simulation)

    time.sleep(0.8)

    print("Generating Families ...")

    time.sleep(0.8)

    for _ in tqdm.trange(total_time_steps):  # type: ignore
        simulation.step()


def run_visualization(simulation: Simulation) -> None:
    """Runs the simulation within a PyGame game."""
    # Import game below since PyGame requires addition loading time
    import minerva.constants  # pylint: disable=C0415
    from minerva.viz.game import Game  # pylint: disable=C0415

    minerva.constants.SHOW_DEBUG = TRUE

    print("Initializing Data ...")
    simulation.initialize_content()

    time.sleep(0.1)

    print("Generating Map and Territories ...")
    generate_world_map(simulation)

    time.sleep(0.8)

    print("Generating Families ...")

    time.sleep(0.8)

    game = Game(simulation)
    game.run()


if __name__ == "__main__":
    sim = Simulation(
        Config(
            n_sovereign_clans=12,
            world_size=(25, 15),
            logging_enabled=LOGGING_ENABLED,
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

    if ENABLE_PROFILING:
        run_simulation_with_profiling(sim)
    elif USE_VIZ:
        run_visualization(sim)
    else:
        run_simulation(sim)

    sim.export_db(DB_OUTPUT_PATH)

"""Minerva Sample: House of the Dragon/Game of Thrones."""

import pathlib
import pstats
from cProfile import Profile
from datetime import datetime

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
from minerva.simulation import Simulation

DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
DB_OUTPUT_PATH = str(pathlib.Path(__file__).parent / "shogun.db")
YEARS = 10
ENABLE_PROFILING = False

if __name__ == "__main__":
    sim = Simulation(Config())

    load_male_first_names(sim, DATA_DIR / "masculine_japanese_names.txt")
    load_female_first_names(sim, DATA_DIR / "feminine_japanese_names.txt")
    load_surnames(sim, DATA_DIR / "japanese_surnames.txt")
    load_settlement_names(sim, DATA_DIR / "japanese_city_names.txt")
    load_clan_names(sim, DATA_DIR / "japanese_surnames.txt")
    load_species_types(sim, DATA_DIR / "species_types.yaml")
    load_traits(sim, DATA_DIR / "ck3_traits.yaml")
    load_businesses_types(sim, DATA_DIR / "ds_business_types.yaml")
    load_occupation_types(sim, DATA_DIR / "ds_occupation_types.yaml")

    total_time_steps: int = YEARS * MONTHS_PER_YEAR

    if ENABLE_PROFILING:
        with Profile() as profile:
            sim.initialize()

            for _ in tqdm.trange(total_time_steps):
                sim.step()

            profile_path = f"profile_{datetime.now().strftime('%Y%m%d_%H_%M')}.prof"

            (
                pstats.Stats(profile)
                .strip_dirs()  # type: ignore
                .sort_stats(pstats.SortKey.PCALLS)
                .dump_stats(profile_path)
            )

    else:
        sim.initialize()

        for _ in tqdm.trange(total_time_steps):
            sim.step()

    sim.export_db(DB_OUTPUT_PATH)

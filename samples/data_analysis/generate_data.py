"""Generate data for training the auto encoder."""

import csv
import pathlib
import random

import numpy as np
import numpy.typing as npt
import tqdm
from feature_extraction import get_default_vector_factory

from minerva.characters.components import Character
from minerva.config import Config
from minerva.data import ck3_traits, japanese_city_names, japanese_names
from minerva.pcg.character import generate_initial_families
from minerva.pcg.world_map import generate_world_map
from minerva.simulation import Simulation

# How many simulations to aggregate
N_SIMULATION_RUNS = 50

# How many years of history to generate
YEAR_TO_SIMULATE = 100

# The world seeds to use for data generation.
WORLD_SEEDS = list(random.sample(range(1000), N_SIMULATION_RUNS))

# File path for CSV output
OUTPUT_PATH = pathlib.Path(__file__).parent / "output.csv"


def main():
    """Main Function."""

    character_feature_vectors: list[npt.NDArray[np.float32]] = []

    vect_factory = get_default_vector_factory()

    n_completed_simulations: int = 0

    # Run simulations for each seed
    for seed in WORLD_SEEDS:
        sim = Simulation(
            Config(
                seed=seed,
                world_size=(25, 15),
                logging_enabled=False,
            )
        )

        japanese_city_names.load_names(sim.world)
        japanese_names.load_names(sim.world)
        ck3_traits.load_traits(sim.world)

        print(f"Running simulation with seed: {seed}")

        generate_world_map(sim.world)
        generate_initial_families(sim.world)

        try:
            for _ in tqdm.trange(YEAR_TO_SIMULATE * 12):
                sim.step()
            n_completed_simulations += 1
        except RuntimeError as exc:
            print(exc)
            continue

        # Print the number of generated characters
        generated_characters = sim.world.get_components((Character,))
        print(f"Total generated characters: {len(generated_characters)}.")
        print("===")

        for _, (character,) in generated_characters:
            character_feature_vectors.append(
                vect_factory.create_feature_vector(character.gameobject)
            )

    # Write each numpy array as a row in the CSV file
    if OUTPUT_PATH.exists():
        OUTPUT_PATH.unlink()

    with open(OUTPUT_PATH, mode="w", newline="", encoding="utf8") as file:
        writer = csv.writer(file)
        writer.writerow(vect_factory.get_column_headers())
        for array in character_feature_vectors:
            writer.writerow(array)

    print("Done.")
    print(f"Completed {n_completed_simulations} simulations")
    print(f"Generated {len(character_feature_vectors)} characters")


if __name__ == "__main__":
    main()

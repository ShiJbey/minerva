"""Run Anomaly Detection using a model."""

import pathlib
import sys

import numpy as np
import tqdm
from anomaly_model import MinervaAnomalyDetector

from minerva.characters.components import Character, HeadOfFamily
from minerva.config import Config
from minerva.data import ck3_traits, japanese_city_names, japanese_names
from minerva.ecs import Active
from minerva.inspection import SimulationInspector
from minerva.pcg.character import generate_initial_families
from minerva.pcg.world_map import generate_world_map
from minerva.simulation import Simulation

# DETECTOR_CONFIG_PATH = pathlib.Path(__file__).parent / "detector.conf.json"
DETECTOR_CONFIG_PATH = pathlib.Path(__file__).parent / "family_head_only_detector.json"
SEED = 12345
YEARS_TO_SIMULATE = 100


if __name__ == "__main__":
    detector = MinervaAnomalyDetector.load(DETECTOR_CONFIG_PATH)

    sim = Simulation(
        Config(
            seed=SEED, world_size=(25, 15), logging_enabled=True, log_to_terminal=False
        )
    )

    japanese_city_names.load_names(sim.world)
    japanese_names.load_names(sim.world)
    ck3_traits.load_traits(sim.world)

    print(f"Running simulation with seed: {SEED}")

    generate_world_map(sim.world)
    generate_initial_families(sim.world)

    try:
        for _ in tqdm.trange(YEARS_TO_SIMULATE * 12):
            sim.step()
    except RuntimeError:
        print("Encountered  runtime error.")
        sys.exit(1)

    # Run prediction on the family heads
    for _, (character, _) in sim.world.get_components((Character, Active)):
        if not character.gameobject.has_component(HeadOfFamily):
            continue

        is_anomaly, justification = detector.predict(character.gameobject)

        if is_anomaly:
            why = ", ".join(
                np.array(detector.vector_factory.get_column_headers())[
                    justification
                ].tolist()
            )
            print(
                f"{character.gameobject.name_with_uid} is an anomaly. Anomalous Features:{why}."
            )

    inspector = SimulationInspector(sim)

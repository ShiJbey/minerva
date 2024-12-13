"""Run Anomaly Detection using a model."""

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import rich
import rich.table
import tqdm
from anomaly_model import MinervaAnomalyDetector

from minerva.characters.components import Character, FormerFamilyHead, HeadOfFamily
from minerva.config import Config
from minerva.data import ck3_traits, japanese_city_names, japanese_names
from minerva.inspection import SimulationInspector
from minerva.simulation import Simulation

SEED = 12345
YEARS_TO_SIMULATE = 100


def create_and_run_simulation() -> Simulation:
    """Create and run the simulation."""
    sim = Simulation(
        Config(
            # seed=SEED,
            world_size=(25, 15),
            logging_enabled=True,
            log_to_terminal=False,
        )
    )

    japanese_city_names.load_names(sim.world)
    japanese_names.load_names(sim.world)
    ck3_traits.load_traits(sim.world)

    print(f"Running simulation with seed: {SEED}")

    for _ in tqdm.trange(YEARS_TO_SIMULATE * 12):
        sim.step()

    return sim


def plot_predictions(
    detector: MinervaAnomalyDetector, error_values: list[float], title: str
):
    """Print Predictions for anomalies."""

    plt.style.use("fivethirtyeight")
    # plt.ylim((0, 6))
    plt.xlabel("Characters")  # type: ignore
    plt.ylabel("Reconstruction Loss")  # type: ignore

    # Plotting the last 100 values
    plt.scatter(  # type: ignore
        list(range(len(error_values))),
        error_values,
        label="Characters",
    )

    plt.axhline(  # type: ignore
        y=detector.error_threshold,
        color="r",
        linestyle="-",
        label="Outlier Threshold",
    )
    plt.title(title)  # type: ignore
    plt.show()  # type: ignore


def evaluate_detector_on_family_heads(
    detector: MinervaAnomalyDetector,
    sim: Simulation,
    figure_title: str,
):
    """Evaluate the performance of a detector on family heads."""
    error_values: list[float] = []
    n_anomalies: int = 0

    console = rich.console.Console()
    table = rich.table.Table("Character", "MSE", "Reason(s)", title=figure_title)

    for _, (character,) in sim.world.query_components((Character,)):
        if character.entity.has_component(
            HeadOfFamily
        ) or character.entity.has_component(FormerFamilyHead):
            is_anomaly, error, justification = detector.predict(character.entity)

            error_values.append(error)

            if is_anomaly:
                justification_str = ", ".join(
                    np.array(detector.vector_factory.get_column_headers())[
                        justification
                    ].tolist()
                )

                table.add_row(
                    character.entity.name_with_uid, str(error), justification_str
                )
                n_anomalies += 1

    percent_anomalies = 100 * (n_anomalies / len(error_values))
    console.print(table)
    console.print(f"[bold orange]% Anomalies[/bold orange] {percent_anomalies}%")

    plot_predictions(detector, error_values, figure_title)


def evaluate_detector_on_bg_npcs(
    detector: MinervaAnomalyDetector,
    sim: Simulation,
    figure_title: str,
):
    """Evaluate the performance od a detector on background NPCs."""
    error_values: list[float] = []
    n_anomalies: int = 0

    console = rich.console.Console()
    table = rich.table.Table("Character", "MSE", "Reason(s)", title=figure_title)

    for _, (character,) in sim.world.query_components((Character,)):
        if not (
            character.entity.has_component(HeadOfFamily)
            or character.entity.has_component(FormerFamilyHead)
        ):
            is_anomaly, error, justification = detector.predict(character.entity)

            error_values.append(error)

            if is_anomaly:
                justification_str = ", ".join(
                    np.array(detector.vector_factory.get_column_headers())[
                        justification
                    ].tolist()
                )

                table.add_row(
                    character.entity.name_with_uid, str(error), justification_str
                )
                n_anomalies += 1

    percent_anomalies = 100 * (n_anomalies / len(error_values))
    console.print(table)
    console.print(f"[bold orange]% Anomalies[/bold orange] {percent_anomalies}%")

    plot_predictions(detector, error_values, figure_title)


if __name__ == "__main__":
    mixed_detector = MinervaAnomalyDetector.load(
        pathlib.Path(__file__).parent / "mixed_detector.json"
    )

    head_only_detector = MinervaAnomalyDetector.load(
        pathlib.Path(__file__).parent / "family_head_only_detector.json"
    )

    bg_character_detector = MinervaAnomalyDetector.load(
        pathlib.Path(__file__).parent / "normies_only_detector.json"
    )

    simulation = create_and_run_simulation()

    # Run prediction on the family heads
    evaluate_detector_on_family_heads(
        mixed_detector,
        simulation,
        "Mixed Model Prediction (Family Heads)",
    )

    evaluate_detector_on_bg_npcs(
        mixed_detector,
        simulation,
        "Mixed Model Prediction (BG NPCs)",
    )

    evaluate_detector_on_family_heads(
        head_only_detector,
        simulation,
        "Family Head Model Prediction (Family Heads)",
    )

    evaluate_detector_on_bg_npcs(
        bg_character_detector,
        simulation,
        "BG NPC Model Prediction (BG NPCs)",
    )

    evaluate_detector_on_bg_npcs(
        head_only_detector,
        simulation,
        "Family Head Model Prediction (BG NPCs)",
    )

    inspector = SimulationInspector(simulation)

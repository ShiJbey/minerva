# type: ignore

"""Minerva Data Analysis Module.

This module is an adaptation of data_analysis.py from neighborly.
I adjusted the classes to work exclusively with drolta and sifting
patterns for one of the final studies of my dissertation.
"""

import math
from typing import Callable, Literal, Optional

import numpy as np
import tqdm
import matplotlib.pyplot as plt

from minerva.characters.components import Character, HeadOfFamily
from minerva.ecs import Active
from minerva.sim_db import SimDB
from minerva.simulation import Simulation


class SiftingPattern:
    """A single sifting pattern to run against a simulation."""

    __slots__ = ("name", "query")

    name: str
    """The name associated with this pattern."""
    query: str
    """The drolta query used to find the pattern."""

    def __init__(self, name: str, query: str) -> None:
        self.name = name
        self.query = query


class BatchSiftingResultEntry:
    """A single entry inside a BatchSiftingResult"""

    __slots__ = ("world_seed", "counts", "population_size")

    world_seed: str
    """The world seed that produced the data."""
    counts: dict[str, int]
    """Sifting pattern names mapped to the number of instances found."""
    population_size: int
    """The number of active characters at the time of sifting."""

    def __init__(self, world_seed: str, population_size: int) -> None:
        self.world_seed = world_seed
        self.population_size = population_size
        self.counts = {}

    def get_per_capita_counts(self) -> dict[str, float]:
        """Calculate per-capita counts for each pattern."""
        return {
            name: (float(count) / self.population_size)
            for name, count in self.counts.items()
        }


class BatchSiftingResult:
    """Resulting data from batch sifting simulations."""

    __slots__ = ("samples", "aggregate_counts")

    samples: list[BatchSiftingResultEntry]
    """Story sifting results per simulation instance."""

    def __init__(self) -> None:
        self.samples = []

    def get_raw_count_median(self) -> dict[str, float]:
        """Calculate the median of the raw counts for each sifting pattern."""

        all_counts: dict[str, list[int]] = {}

        for sample in self.samples:
            for name, count in sample.counts.items():
                if name not in all_counts:
                    all_counts[name] = []

                all_counts[name].append(count)

        median_scores = {
            name: float(np.median(counts)) for name, counts in all_counts.items()
        }

        return median_scores

    def get_raw_count_distribution(self) -> dict[str, tuple[float, float]]:
        """Calculate the mean and std error for each sifting pattern."""

        all_counts: dict[str, list[int]] = {}

        for sample in self.samples:
            for name, count in sample.counts.items():
                if name not in all_counts:
                    all_counts[name] = []

                all_counts[name].append(count)

        score_distributions = {
            name: (
                float(np.mean(counts)),
                float(np.std(counts, ddof=1)) / math.sqrt(len(counts)),
            )
            for name, counts in all_counts.items()
        }

        return score_distributions

    def get_per_capita_median(self) -> dict[str, float]:
        """Calculate the median of the per-capita counts for each sifting pattern."""

        all_counts: dict[str, list[float]] = {}

        for sample in self.samples:
            for name, count in sample.get_per_capita_counts().items():
                if name not in all_counts:
                    all_counts[name] = []

                all_counts[name].append(count)

        median_scores = {
            name: float(np.median(counts)) for name, counts in all_counts.items()
        }

        return median_scores

    def get_per_capita_distribution(self) -> dict[str, tuple[float, float]]:
        """Calculate the mean and std error of the per-capita pattern counts."""

        all_counts: dict[str, list[float]] = {}

        for sample in self.samples:
            for name, count in sample.get_per_capita_counts().items():
                if name not in all_counts:
                    all_counts[name] = []

                all_counts[name].append(count)

        score_distributions = {
            name: (
                float(np.mean(counts)),
                float(np.std(counts, ddof=1)) / math.sqrt(len(counts)),
            )
            for name, counts in all_counts.items()
        }

        return score_distributions


def _get_sim_population(sim: Simulation) -> int:
    """Get the population of living characters in the simulation."""
    return len(list(sim.world.query_components((Character, Active))))


def batch_sift_simulations(
    factory: Callable[[], Simulation],
    n_instances: int,
    years: int,
    sifting_patterns: list[SiftingPattern],
) -> BatchSiftingResult:
    """Run multiple simulations and collect/aggregate data from each.

    Parameters
    ----------
    factory
        A callable that constructs and configures a new simulation.
    n_instances
        The number of simulation instances to run.
    years
        The number of years to elapse before collecting data from each simulation.
    sifting_patterns
        Sifting patterns to run against each simulation instance.

    Returns
    -------
    BatchSiftingResults
        Aggregate and per-simulation story sifting counts and metrics.
    """
    result = BatchSiftingResult()

    for i in range(n_instances):
        sim = factory()
        print(f"Instance: {i}, World Seed: {sim.config.seed}")
        for _ in tqdm.tqdm(range(years)):
            sim.step()

        result_entry = BatchSiftingResultEntry(
            str(sim.config.seed), _get_sim_population(sim)
        )

        query_engine = sim.world.get_resource(SimDB).query_engine
        db_conn = sim.world.get_resource(SimDB).conn
        for pattern in sifting_patterns:
            pattern_count: int = len(
                query_engine.query(pattern.query, db_conn).fetch_all()
            )
            result_entry.counts[pattern.name] = pattern_count

        result.samples.append(result_entry)

    return result


def display_bar_chart(
    batch_result: BatchSiftingResult,
    operation: Literal["raw", "per_capita"] = "raw",
    include: Optional[list[str]] = None,
    exclude: Optional[list[str]] = None,
) -> None:
    """Display a bar chart of the sifting results.

    Parameters
    ----------
    batch_result
        The resulting counts from the sifting patterns
    operation
        What results should be displayed (raw counts or per-capita counts)
    include
        Names of patterns to include in the histogram. Only names in this
        list will be displayed. If this parameter is not set, then all
        patterns are included in the output.
    exclude
        Exclude the patterns with the given names from the output. If this
        parameter is not supplied, all patterns are included in the output.
        If exclude and include are both provided, include takes precedence.
    """

    include_set_given: bool = include is not None
    exclude_set_given: bool = exclude is not None
    include_set: set[str] = set(include if include is not None else [])
    exclude_set: set[str] = set(exclude if exclude is not None else [])

    data: dict[str, tuple[float, float]]
    if operation == "raw":
        data = batch_result.get_raw_count_distribution()
    else:
        data = batch_result.get_per_capita_distribution()

    if include_set_given:
        data = {key: value for key, value in data.items() if key in include_set}

    if exclude_set_given:
        data = {key: value for key, value in data.items() if key not in exclude_set}

    categories: list[str] = []
    values: list[float] = []
    errors: list[float] = []

    # Divide the data into separate lists to be passed to matplotlib
    for name, (mean, std) in data.items():
        categories.append(name)
        values.append(mean)
        errors.append(std)

    fig, ax = plt.subplots(1, 1, figsize=(16, 10))  # type: ignore
    bars = ax.barh(  # type: ignore
        categories,
        values,
        yerr=errors,
        color="skyblue",
        edgecolor="black",
    )
    ax.set_ylabel("Patterns")  # type: ignore
    # plt.xticks(rotation=45, ha="right")
    if operation == "raw":
        ax.set_xlabel("Raw Count Mean")  # type: ignore
        ax.set_title("Sifting Pattern Raw Mean Counts")  # type: ignore
    else:
        ax.set_xlabel("Per-Capita Count Mean")  # type: ignore
        ax.set_title("Sifting Pattern Mean Per-Capita Counts")  # type: ignore
    plt.tight_layout()
    plt.show()  # type: ignore


def validate_between(
    batch_result: BatchSiftingResult,
    patterns: list[str],
    upper_bound: float,
    lower_bound: float,
    operation: Literal["raw", "per_capita"] = "raw",
    display_result: bool = True,
) -> bool:
    """Validate that the values for the results are between the bounds.

    Parameters
    ----------
    batch_result
        The result from sifting multiple simulations
    patterns
        The names of patterns to validate
    upper_bound
        The maximum count/value for a bar
    lower_bound
        The minimum count/value for a bar
    operation
        What results should be displayed (raw counts or per-capita counts)
    display_result
        Show the result of the validation in a plot

    Returns
    -------
    bool
        True if the patterns passed the validation, False otherwise.
    """
    if len(patterns) == 0:
        raise ValueError("No patterns provided to validation check.")

    include_set: set[str] = set(patterns)

    data: dict[str, tuple[float, float]]
    if operation == "raw":
        data = batch_result.get_raw_count_distribution()
    else:
        data = batch_result.get_per_capita_distribution()

    data = {key: value for key, value in data.items() if key in include_set}

    validation_passed = True

    for _, (mean, _) in data.items():
        if mean > upper_bound or mean < lower_bound:
            validation_passed = False
            break

    if display_result:
        categories: list[str] = []
        values: list[float] = []
        errors: list[float] = []

        # Divide the data into separate lists to be passed to matplotlib
        for name, (mean, std) in data.items():
            categories.append(name)
            values.append(mean)
            errors.append(std)

        fig, ax = plt.subplots()  # type: ignore

        bars = ax.bar(  # type: ignore
            categories,
            values,
            yerr=errors,
            color="skyblue",
            edgecolor="black",
        )
        ax.set_xlabel("Patterns")  # type: ignore

        plt.xticks(rotation=45, ha="right")

        if operation == "raw":
            ax.set_ylabel("Raw Count Mean")  # type: ignore
            ax.set_title("Validate Between: Raw Mean Counts")  # type: ignore
        else:
            ax.set_ylabel("Per-Capita Count Mean")  # type: ignore
            ax.set_title("Validate Between: Mean Per-Capita Counts")  # type: ignore

        if validation_passed:
            ax.text(
                0.95,
                0.95,
                "Pass",
                transform=ax.transAxes,
                fontsize=14,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(boxstyle="round", facecolor="green", alpha=0.5),
            )
            ax.axhspan(lower_bound, upper_bound, color="green", alpha=0.3)

        else:
            ax.text(
                0.95,
                0.95,
                "Fail",
                transform=ax.transAxes,
                fontsize=14,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(boxstyle="round", facecolor="red", alpha=0.5),
            )
            ax.axhspan(lower_bound, upper_bound, color="red", alpha=0.3)

        plt.show()

    return validation_passed


def validate_above(
    batch_result: BatchSiftingResult,
    patterns: list[str],
    lower_bound: float,
    operation: Literal["raw", "per_capita"] = "raw",
    display_result: bool = True,
) -> bool:
    """Validate that the values for the results are above a lower-bound.

    Parameters
    ----------
    batch_result
        The result from sifting multiple simulations
    patterns
        The names of patterns to validate
    lower_bound
        The minimum count/value for a bar
    operation
        What results should be displayed (raw counts or per-capita counts)
    display_result
        Show the result of the validation in a plot

    Returns
    -------
    bool
        True if the patterns passed the validation, False otherwise.
    """
    if len(patterns) == 0:
        raise ValueError("No patterns provided to validation check.")

    include_set: set[str] = set(patterns)

    data: dict[str, tuple[float, float]]
    if operation == "raw":
        data = batch_result.get_raw_count_distribution()
    else:
        data = batch_result.get_per_capita_distribution()

    data = {key: value for key, value in data.items() if key in include_set}

    validation_passed = True

    for _, (mean, _) in data.items():
        if mean < lower_bound:
            validation_passed = False
            break

    if display_result:
        categories: list[str] = []
        values: list[float] = []
        errors: list[float] = []

        # Divide the data into separate lists to be passed to matplotlib
        for name, (mean, std) in data.items():
            categories.append(name)
            values.append(mean)
            errors.append(std)

        fig, ax = plt.subplots()  # type: ignore

        ax.axhline(y=lower_bound, color="r", linestyle="-")

        bars = ax.bar(  # type: ignore
            categories,
            values,
            yerr=errors,
            color="skyblue",
            edgecolor="black",
        )
        ax.set_xlabel("Patterns")  # type: ignore

        plt.xticks(rotation=45, ha="right")

        if operation == "raw":
            ax.set_ylabel("Raw Count Mean")  # type: ignore
            ax.set_title("Validate Above:  Raw Mean Counts")  # type: ignore
        else:
            ax.set_ylabel("Per-Capita Count Mean")  # type: ignore
            ax.set_title("Validate Above: Mean Per-Capita Counts")  # type: ignore

        if validation_passed:
            ax.text(
                0.95,
                0.95,
                "Pass",
                transform=ax.transAxes,
                fontsize=14,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(boxstyle="round", facecolor="green", alpha=0.5),
            )

        else:
            ax.text(
                0.95,
                0.95,
                "Fail",
                transform=ax.transAxes,
                fontsize=14,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(boxstyle="round", facecolor="red", alpha=0.5),
            )

        plt.show()

    return validation_passed


def validate_below(
    batch_result: BatchSiftingResult,
    patterns: list[str],
    upper_bound: float,
    operation: Literal["raw", "per_capita"] = "raw",
    display_result: bool = True,
) -> bool:
    """Validate that the values for the results are between the bounds.

    Parameters
    ----------
    batch_result
        The result from sifting multiple simulations
    patterns
        The names of patterns to validate
    upper_bound
        The maximum count/value for a bar
    operation
        What results should be displayed (raw counts or per-capita counts)
    display_result
        Show the result of the validation in a plot

    Returns
    -------
    bool
        True if the patterns passed the validation, False otherwise.
    """
    if len(patterns) == 0:
        raise ValueError("No patterns provided to validation check.")

    include_set: set[str] = set(patterns)

    data: dict[str, tuple[float, float]]
    if operation == "raw":
        data = batch_result.get_raw_count_distribution()
    else:
        data = batch_result.get_per_capita_distribution()

    data = {key: value for key, value in data.items() if key in include_set}

    validation_passed = True

    for _, (mean, _) in data.items():
        if mean > upper_bound:
            validation_passed = False
            break

    if display_result:
        categories: list[str] = []
        values: list[float] = []
        errors: list[float] = []

        # Divide the data into separate lists to be passed to matplotlib
        for name, (mean, std) in data.items():
            categories.append(name)
            values.append(mean)
            errors.append(std)

        fig, ax = plt.subplots()  # type: ignore

        ax.axhline(y=upper_bound, color="r", linestyle="-")

        bars = ax.bar(  # type: ignore
            categories,
            values,
            yerr=errors,
            color="skyblue",
            edgecolor="black",
        )
        ax.set_xlabel("Patterns")  # type: ignore

        plt.xticks(rotation=45, ha="right")

        if operation == "raw":
            ax.set_ylabel("Raw Count Mean")  # type: ignore
            ax.set_title("Validate Below: Raw Mean Counts")  # type: ignore
        else:
            ax.set_ylabel("Per-Capita Count Mean")  # type: ignore
            ax.set_title("Validate Below: Mean Per-Capita Counts")  # type: ignore

        if validation_passed:
            ax.text(
                0.95,
                0.95,
                "Pass",
                transform=ax.transAxes,
                fontsize=14,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(boxstyle="round", facecolor="green", alpha=0.5),
            )

        else:
            ax.text(
                0.95,
                0.95,
                "Fail",
                transform=ax.transAxes,
                fontsize=14,
                verticalalignment="top",
                horizontalalignment="right",
                bbox=dict(boxstyle="round", facecolor="red", alpha=0.5),
            )

        plt.show()

    return validation_passed

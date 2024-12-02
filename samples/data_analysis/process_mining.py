"""Example Process Mining using Minerva Data.

This sample script reimplements some of the process mining functionality found in PM4PY.
Unfortunately, pm4py does not work with Minerva's timestamp representation. Pandas can
only represent a limited span of dates and 0001-01 falls outside of that interval. The
code below finds the starting and ending events of each process and extracts a directly-
follows graph from life event data from minerva. The extracted data is passed to pm4py
for visualization.

"""

import pathlib
import sqlite3
import sys
from collections import defaultdict
from pprint import pprint

import pandas as pd
import pm4py

# This
DB_PATH = pathlib.Path(__file__).parent.parent / "shogun.db"


def get_start_events(
    event_log: pd.DataFrame,
    event_key: str,
    case_id_key: str,
    timestamp_key: str,
) -> dict[str, int]:
    """Get the events that mark the beginning of processes.

    Parameters
    ----------
    event_log
        Event information stored in a dataframe. It must have columns containing
        the type of event, the case ID (entity ID), and a timestamp.
    event_key
        The key used to access the event type column in the event log dataframe.
    case_id_key
        The key used to access the case ID column in the event log dataframe.
    timestamp_key
        The key used to access the timestamp column in the event log dataframe.

    Returns
    -------
    dict[str, int]
        Event type names mapped to the number of cases that start with that event.
    """
    start_events: defaultdict[str, int] = defaultdict(lambda: 0)

    case_ids = event_log[case_id_key].unique()  # type: ignore
    case_ids.sort()

    for case_id in case_ids:
        case_data = event_log[event_log[case_id_key] == case_id]  # type: ignore
        case_data = case_data.sort_values(by=[timestamp_key])  # type: ignore
        first_event_type = case_data.iloc[0][event_key]  # type: ignore
        start_events[first_event_type] += 1

    return {**start_events}


def get_end_events(
    event_log: pd.DataFrame,
    event_key: str,
    case_id_key: str,
    timestamp_key: str,
) -> dict[str, int]:
    """Get the events that mark the end of processes.

    Parameters
    ----------
    event_log
        Event information stored in a dataframe. It must have columns containing
        the type of event, the case ID (entity ID), and a timestamp.
    event_key
        The key used to access the event type column in the event log dataframe.
    case_id_key
        The key used to access the case ID column in the event log dataframe.
    timestamp_key
        The key used to access the timestamp column in the event log dataframe.

    Returns
    -------
    dict[str, int]
        Event type names mapped to the number of cases that ended with that event.
    """
    end_events: defaultdict[str, int] = defaultdict(lambda: 0)

    case_ids = event_log[case_id_key].unique()  # type: ignore
    case_ids.sort()

    for case_id in case_ids:
        case_data = event_log[event_log[case_id_key] == case_id]  # type: ignore
        case_data = case_data.sort_values(by=[timestamp_key], ascending=False)  # type: ignore
        first_event_type = case_data.iloc[0][event_key]  # type: ignore
        end_events[first_event_type] += 1

    return {**end_events}


def extract_dfg(
    event_log: pd.DataFrame,
    event_key: str,
    case_id_key: str,
    timestamp_key: str,
) -> dict[tuple[str, str], int]:
    """Discover a directly-follows graph for the provided event data.

    Parameters
    ----------
    event_log
        Event information stored in a dataframe. It must have columns containing
        the type of event, the case ID (entity ID), and a timestamp.
    event_key
        The key used to access the event type column in the event log dataframe.
    case_id_key
        The key used to access the case ID column in the event log dataframe.
    timestamp_key
        The key used to access the timestamp column in the event log dataframe.

    Returns
    -------
    dict[[str, str], int]
        Connections between event types (A to B) represented as tuples mapped to
        the number of cases that contain that transition from event A to B.
    """
    event_transitions: defaultdict[tuple[str, str], int] = defaultdict(lambda: 0)

    case_ids = event_log[case_id_key].unique()  # type: ignore
    case_ids.sort()

    for case_id in case_ids:
        case_data: pd.DataFrame = event_log[event_log[case_id_key] == case_id]  # type: ignore
        case_data: pd.DataFrame = case_data.sort_values(  # type: ignore
            by=[timestamp_key]
        )

        num_events: int = case_data.shape[0]  # type: ignore

        if num_events < 1:
            continue

        for i in range(1, num_events):  # type: ignore
            event_a: str = case_data.iloc[i - 1][event_key]  # type: ignore
            event_b: str = case_data.iloc[i][event_key]  # type: ignore
            event_transitions[(event_a, event_b)] += 1

    return {**event_transitions}


def main():
    """main function."""

    if not DB_PATH.is_file():
        print(f"Cannot find DB file at : {DB_PATH}")
        print("Please run the shogun.py sample to generate the shogun.db file.")
        sys.exit(1)

    db = sqlite3.connect(DB_PATH)

    event_log: pd.DataFrame = pd.read_sql_query(  # type: ignore
        "SELECT subject_id as case_id, event_type, timestamp FROM life_events", db
    )

    num_events = len(event_log)
    num_cases = len(event_log.case_id.unique())  # type: ignore
    print(f"Number of events: {num_events}")
    print(f"Number of cases: {num_cases}")

    start_activities = get_start_events(
        event_log,
        event_key="event_type",
        case_id_key="case_id",
        timestamp_key="timestamp",
    )

    print("Start activities:")
    pprint(start_activities)

    end_activities = get_end_events(
        event_log,
        event_key="event_type",
        case_id_key="case_id",
        timestamp_key="timestamp",
    )

    print("End activities:")
    pprint(end_activities)

    dfg = extract_dfg(
        event_log,
        event_key="event_type",
        case_id_key="case_id",
        timestamp_key="timestamp",
    )

    pm4py.view_dfg(dfg, start_activities, end_activities)  # type: ignore


if __name__ == "__main__":
    main()

"""Life Event System.

Life events are the building block of story generation. We set them apart from the
ECS-related events by requiring that each have a timestamp of the in-simulation date
they were emitted.

"""

from __future__ import annotations

import logging
from abc import ABC
from typing import ClassVar, Optional

from minerva.datetime import SimDate
from minerva.ecs import Entity, World
from minerva.sim_db import SimDB

_logger = logging.getLogger(__name__)


class LifeEventType:
    """Configuration data about a type of life event.

    This data is pre-registered with the simulation's database to save
    memory and help with data visualization.

    The description template uses a simple string substitution function.
    For example, the string '{subject_name} ({subject_id}) became ruler.',
    would expand to 'Rhaenyra (13) became ruler.' Assuming subject_name and
    subject_id are arguments associated with the event in the event_args table
    of the database.
    """

    __slots__ = ("name", "display_name", "description")

    name: str
    """A unique text name for this life event."""
    display_name: str
    """The name of the event when displayed in a GUI."""
    description: str
    """A text template used to generate a textual description of this event type."""

    def __init__(
        self,
        name: str,
        display_name: str,
        description: str,
    ) -> None:
        self.name = name
        self.display_name = display_name
        self.description = description


def register_life_event_type(world: World, life_event_type: LifeEventType) -> None:
    """Registers a life event type with the simulation's database."""
    db = world.get_resource(SimDB).db
    cursor = db.cursor()

    cursor.execute(
        """
        INSERT INTO life_event_types (name, display_name, description)
        VALUES (?, ?, ?);
        """,
        (
            life_event_type.name,
            life_event_type.display_name,
            life_event_type.description,
        ),
    )

    db.commit()


class LifeEvent(ABC):
    """An event of significant importance in an entity's life"""

    _next_life_event_id: ClassVar[int] = 1

    __slots__ = (
        "world",
        "subject",
        "event_id",
        "event_type",
        "timestamp",
        "event_args",
    )

    world: World
    """The simulation's world instance."""
    subject: Entity
    """What/Who is the event about."""
    event_id: int
    """Numerical ID of this life event."""
    event_type: str
    """Name of the life event type in teh database."""
    timestamp: SimDate
    """The timestamp of the event."""
    event_args: dict[str, str]
    """Arguments passed to the database."""

    def __init__(self, event_type: str, subject: Entity) -> None:
        self.world = subject.world
        self.subject = subject
        self.event_id = LifeEvent._next_life_event_id
        LifeEvent._next_life_event_id += 1
        self.event_type = event_type
        self.timestamp = subject.world.get_resource(SimDate).copy()
        self.event_args = {"subject_name": subject.name, "subject_id": str(subject.uid)}

    def log_event(self) -> None:
        """Dispatches the event to the proper listeners."""

        db = self.world.get_resource(SimDB).db
        cur = db.cursor()

        cur.execute(
            """
            INSERT INTO life_events (event_id, subject_id, event_type, timestamp)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.subject.uid,
                self.event_type,
                self.timestamp.to_iso_str(),
            ),
        )

        cur.executemany(
            """
            INSERT INTO life_event_args (event_id, name, value)
            VALUES (?, ?, ?);
            """,
            [(self.event_id, k, v) for k, v in self.event_args.items()],
        )

        db.commit()

        _logger.info(
            "[%s]: %s",
            str(self.timestamp),
            get_life_event_description(self.world, self.event_id),
        )

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.event_id}, "
            f" timestamp={self.timestamp!r})"
        )

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__}(id={self.event_id}, "
            f" timestamp={self.timestamp!r})"
        )


def get_life_event_timestamp(world: World, event_id: int) -> SimDate:
    """Get the timestamp for the life event with the given event ID."""

    db = world.get_resource(SimDB).db
    cursor = db.cursor()

    # First get the event information
    timestamp: str = cursor.execute(
        """
        SELECT
            timestamp
        FROM life_events
        WHERE life_events.event_id=?;
        """,
        (event_id,),
    ).fetchone()[0]

    return SimDate.from_iso_str(timestamp)


def get_life_event_description(world: World, event_id: int) -> str:
    """Get the description for the life event with the given event ID."""

    db = world.get_resource(SimDB).db
    cursor = db.cursor()

    # First get the event information
    result: Optional[tuple[str,]] = cursor.execute(
        """
        SELECT
            life_event_types.description
        FROM life_events
        JOIN life_event_types ON life_events.event_type=life_event_types.name
        WHERE life_events.event_id=?;
        """,
        (event_id,),
    ).fetchone()

    if result is None:
        raise ValueError(f"Cannot find description template for: {event_id}")

    description_template = result[0]

    event_args: list[tuple[str, str]] = cursor.execute(
        """
        SELECT
            name,
            value
        FROM life_event_args
        WHERE event_id=?;
        """,
        (event_id,),
    ).fetchall()

    final_description = description_template
    for k, v in event_args:
        final_description = final_description.replace("{" + k + "}", v)

    return final_description


def get_life_event_ids(entity: Entity) -> list[int]:
    """Get the IDs for all life events related"""

    world = entity.world
    db = world.get_resource(SimDB).db
    cursor = db.cursor()

    result: list[tuple[int,]] = cursor.execute(
        """
        SELECT event_id FROM life_events WHERE subject_id=?;
        """,
        (entity.uid,),
    ).fetchall()

    return [r[0] for r in result]

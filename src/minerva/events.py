# pylint: disable=C0209, C0302
"""Data classes for logging action events."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Optional

from minerva.characters.components import Family
from minerva.ecs import Component, Entity, World
from minerva.game_state import GameState
from minerva.sim_db import SimDB

_logger = logging.getLogger(__name__)


class GlobalEventHistory:
    """Global history or all logged events."""

    __slots__ = ("events",)

    events: dict[int, Event]

    def __init__(self) -> None:
        self.events = {}

    def add_event(self, event: Event) -> None:
        """Add an event to the history."""
        self.events[event.uid] = event

    def get_event(self, event_id: int) -> Event:
        """Get an event by it's ID."""
        return self.events[event_id]


class EventHistory(Component):
    """Tracks events associated with this entity."""

    __slots__ = ("_event_ids",)

    _event_ids: list[int]

    def __init__(self) -> None:
        super().__init__()
        self._event_ids = []

    def append(self, event_id: int) -> None:
        """Add an event ID to the history."""
        self._event_ids.append(event_id)

    def get_events(self) -> list[int]:
        """Get all events in the history."""
        return self._event_ids


class Event(ABC):
    """An event logged by the simulation.

    Events are logged within
    """

    __slots__ = ("uid", "world", "timestamp", "logged_to")

    uid: int
    world: World
    timestamp: int
    logged_to: list[Entity]

    def __init__(self, world: World) -> None:
        self.uid = Event._get_next_event_uid(world)
        self.world = world
        self.timestamp = world.get_resource(GameState).year
        self.logged_to = []

    @staticmethod
    def _get_next_event_uid(world: World) -> int:
        """Get next UID for event."""

        game_state = world.get_resource(GameState)
        uid = game_state.next_event_uid
        game_state.next_event_uid += 1
        return uid

    @abstractmethod
    def get_description(self) -> str:
        """Get the description of the event."""
        raise NotImplementedError()

    def log_to_db(self) -> None:
        """Log the event to the database."""
        return

    def log_event(self) -> None:
        """Dispatches the event to the proper listeners."""

        description = self.get_description()

        _logger.info("[%04d]: %s", self.timestamp, description)

        self.world.get_resource(GlobalEventHistory).add_event(self)

        for entity in self.logged_to:
            entity.get_component(EventHistory).append(self.uid)

        self.log_to_db()


class BecomeFamilyHeadEvent(Event):
    """Logs a record of a character becoming head of their family."""

    __slots__ = ("character", "family")

    character: Entity
    family: Entity

    def __init__(self, character: Entity, family: Entity) -> None:
        super().__init__(character.world)
        self.character = character
        self.family = family
        self.logged_to = [self.character]

    def get_description(self) -> str:
        return "{} became head of the {} family.".format(
            self.character.name_with_uid, self.family.name_with_uid
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS BecomeFamilyHeadEvent;

                CREATE TABLE BecomeFamilyHeadEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    character INT NOT NULL,
                    family INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (character) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    BecomeFamilyHeadEvent (uid, character, family, timestamp)
                VALUES
                    (?, ?, ?, ?);
                """,
                (self.uid, self.character.uid, self.family, self.timestamp),
            )


class SendGiftEvent(Event):
    """Logs a record of a character sending a gift to another."""

    __slots__ = ("character", "recipient")

    character: Entity
    recipient: Entity

    def __init__(self, character: Entity, recipient: Entity) -> None:
        super().__init__(character.world)
        self.character = character
        self.recipient = recipient
        self.logged_to = [character]

    def get_description(self) -> str:
        return "{} sent a gift to {}".format(
            self.character.name_with_uid, self.recipient.name_with_uid
        )


class SendAidEvent(Event):
    """Logs a record of a character sending a aid to another during a revolt."""

    __slots__ = ("character", "recipient")

    character: Entity
    recipient: Entity

    def __init__(self, character: Entity, recipient: Entity) -> None:
        super().__init__(character.world)
        self.character = character
        self.recipient = recipient
        self.logged_to = [character]

    def get_description(self) -> str:
        return "{} sent aid to {}".format(
            self.character.name_with_uid, self.recipient.name_with_uid
        )


class ExtortTerritoryOwnersEvent(Event):
    """Logs a record of a ruler extorting land-controlling families."""

    __slots__ = ("character",)

    character: Entity

    def __init__(self, character: Entity) -> None:
        super().__init__(character.world)
        self.character = character
        self.logged_to = [character]

    def get_description(self) -> str:
        return "{} extorted the land-controlling families".format(
            self.character.name_with_uid
        )


class ExtortLocalFamiliesEvent(Event):
    """Logs a record of a land-controlling family extorting others on their land."""

    __slots__ = ("character",)

    character: Entity

    def __init__(self, character: Entity) -> None:
        super().__init__(character.world)
        self.character = character
        self.logged_to = [character]

    def get_description(self) -> str:
        return "{} extorted families in their controlled territories.".format(
            self.character.name_with_uid
        )


class DeathEvent(Event):
    """Logs a character's death"""

    __slots__ = ("subject", "cause")

    subject: Entity
    cause: str

    def __init__(self, subject: Entity, cause: str) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.cause = cause
        self.logged_to = [subject]

    def get_description(self) -> str:
        return "{} died (cause: {}).".format(self.subject.name_with_uid, self.cause)

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS DeathEvent;

                CREATE TABLE DeathEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    cause TEXT,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    DeathEvent (uid, subject, cause, timestamp)
                VALUES
                    (?, ?, ?, ?);
                """,
                (self.uid, self.subject.uid, self.cause, self.timestamp),
            )


class BecomeSeniorEvent(Event):
    """Initiator becomes a senior."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character.world)
        self.character = character
        self.logged_to = [character]

    def get_description(self) -> str:
        return "{} became a senior.".format(self.character.name_with_uid)

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS BecomeSeniorEvent;

                CREATE TABLE BecomeSeniorEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    BecomeSeniorEvent (uid, subject, timestamp)
                VALUES
                    (?, ?, ?);
                """,
                (self.uid, self.character.uid, self.timestamp),
            )


class BecomeAdultEvent(Event):
    """Initiator becomes an adult."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character.world)
        self.character = character
        self.logged_to = [character]

    def get_description(self) -> str:
        return "{} became an adult.".format(self.character.name_with_uid)

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS BecomeAdultEvent;

                CREATE TABLE BecomeAdultEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    BecomeAdultEvent (uid, subject, timestamp)
                VALUES
                    (?, ?, ?);
                """,
                (self.uid, self.character.uid, self.timestamp),
            )


class BecomeYoungAdultEvent(Event):
    """Initiator becomes a young adult."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character.world)
        self.character = character
        self.logged_to = [character]

    def get_description(self) -> str:
        return "{} became a young adult.".format(self.character.name_with_uid)

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS BecomeYoungAdultEvent;

                CREATE TABLE BecomeYoungAdultEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    BecomeYoungAdultEvent (uid, subject, timestamp)
                VALUES
                    (?, ?, ?);
                """,
                (self.uid, self.character.uid, self.timestamp),
            )


class BecomeAdolescentEvent(Event):
    """Initiator becomes an adolescent."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character.world)
        self.character = character
        self.logged_to = [character]

    def get_description(self) -> str:
        return "{} became an adolescent.".format(self.character.name_with_uid)

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS BecomeAdolescentEvent;

                CREATE TABLE BecomeAdolescentEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    BecomeAdolescentEvent (uid, subject, timestamp)
                VALUES
                    (?, ?, ?);
                """,
                (self.uid, self.character.uid, self.timestamp),
            )


class BecomeChildEvent(Event):
    """Initiator becomes a child."""

    __slots__ = ("character",)

    def __init__(self, character: Entity) -> None:
        super().__init__(character.world)
        self.character = character
        self.logged_to = [character]

    def get_description(self) -> str:
        return "{} became a child.".format(self.character.name_with_uid)

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS BecomeChildEvent;

                CREATE TABLE BecomeChildEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    BecomeChildEvent (uid, subject, timestamp)
                VALUES
                    (?, ?, ?);
                """,
                (self.uid, self.character.uid, self.timestamp),
            )


class MarriageEvent(Event):
    """Event dispatched when a character gets married."""

    __slots__ = (
        "subject",
        "spouse",
    )

    subject: Entity
    spouse: Entity

    def __init__(self, subject: Entity, spouse: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.spouse = spouse
        self.logged_to = [subject]

    def get_description(self) -> str:
        return "{} married {}.".format(
            self.subject.name_with_uid, self.spouse.name_with_uid
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS MarriageEvent;

                CREATE TABLE MarriageEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    spouse INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid),
                    FOREIGN KEY (spouse) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    MarriageEvent (uid, subject, spouse, timestamp)
                VALUES
                    (?, ?, ?, ?);
                """,
                (self.uid, self.subject.uid, self.spouse.uid, self.timestamp),
            )


class PregnancyEvent(Event):
    """Event dispatched when a character gets pregnant."""

    __slots__ = ("mother", "father")

    def __init__(self, mother: Entity, father: Entity) -> None:
        super().__init__(mother.world)
        self.mother = mother
        self.father = father
        self.logged_to = [self.mother]

    def get_description(self) -> str:
        return "{} got pregnant by {}".format(
            self.mother.name_with_uid,
            self.father.name_with_uid,
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Create a database table for events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS PregnancyEvent;

                CREATE TABLE PregnancyEvent (
                    uid INT PRIMARY KEY,
                    mother INT NOT NULL,
                    father INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (mother) REFERENCES Character(uid),
                    FOREIGN KEY (father) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    PregnancyEvent (uid, mother, father, timestamp)
                VALUES
                    (?, ?, ?, ?);
                """,
                (self.uid, self.mother.uid, self.father.uid, self.timestamp),
            )


class GiveBirthEvent(Event):
    """Event dispatched when a character gives birth to another."""

    __slots__ = ("mother", "child")

    mother: Entity
    child: Entity

    def __init__(self, mother: Entity, child: Entity) -> None:
        super().__init__(mother.world)
        self.mother = mother
        self.child = child
        self.logged_to = [mother]

    def get_description(self) -> str:
        return "{} gave birth to {}.".format(
            self.mother.name_with_uid,
            self.child.name_with_uid,
        )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    GiveBirthEvent(uid, mother, child, timestamp)
                VALUES
                    (?, ?, ?, ?)
                """,
                (self.uid, self.mother.uid, self.child.uid, self.timestamp),
            )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS GiveBirthEvent;

                CREATE TABLE GiveBirthEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    mother INT NOT NULL,
                    child INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (mother) REFERENCES Character(uid),
                    FOREIGN KEY (child) REFERENCES Character(uid)
                ) STRICT;
                """
            )


class TakeControlOfTerritoryEvent(Event):
    """Event dispatched when a family head seizes power over a territory."""

    __slots__ = ("family_head", "family", "territory")

    family_head: Entity
    family: Entity
    territory: Entity

    def __init__(self, family_head: Entity, family: Entity, territory: Entity) -> None:
        super().__init__(family_head.world)
        self.family_head = family_head
        self.territory = territory
        self.family = family
        self.logged_to = [family_head]

    def get_description(self) -> str:
        return "{} took control of the {} territory.".format(
            self.family_head.name_with_uid, self.territory.name_with_uid
        )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    TakeControlOfTerritoryEvent (
                        uid, family_head, family, territory, timestamp
                    )
                VALUES
                    (?, ?, ?)
                """,
                (
                    self.uid,
                    self.family_head.uid,
                    self.family.uid,
                    self.territory.uid,
                    self.timestamp,
                ),
            )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS TakeControlOfTerritoryEvent;

                CREATE TABLE TakeControlOfTerritoryEvent (
                    uid INT PRIMARY KEY,
                    family_head INT NOT NULL,
                    family INT NOT NULL,
                    territory INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (family_head) REFERENCES Character(uid),
                    FOREIGN KEY (family) REFERENCES Family(uid),
                    FOREIGN KEY (territory) REFERENCES Territory(uid)
                ) STRICT;
                """
            )


class LoseControlOfTerritoryEvent(Event):
    """Event dispatched when a family head loses control over a territory."""

    __slots__ = ("family_head", "family", "territory")

    family_head: Optional[Entity]
    family: Entity
    territory: Entity

    def __init__(self, family: Entity, territory: Entity) -> None:
        super().__init__(family.world)
        self.family_head = family.get_component(Family).head
        self.territory = territory
        self.family = family
        if self.family_head is not None:
            self.logged_to = [self.family_head]

    def get_description(self) -> str:
        return "The {} family lost control over the {} territory.".format(
            self.family.name_with_uid,
            self.territory.name_with_uid,
        )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    LoseControlOfTerritoryEvent (
                        uid, family_head, family, territory, timestamp
                    )
                VALUES
                    (?, ?, ?, ?, ?)
                """,
                (
                    self.uid,
                    self.family_head.uid if self.family_head else None,
                    self.family.uid,
                    self.territory.uid,
                    self.timestamp,
                ),
            )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS LoseControlOfTerritoryEvent;

                CREATE TABLE LoseControlOfTerritoryEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    family_head INT,
                    family INT NOT NULL,
                    territory INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (family_head) REFERENCES Character(uid)
                    FOREIGN KEY (family) REFERENCES Family(uid),
                    FOREIGN KEY (territory) REFERENCES Territory(uid)
                ) STRICT;
                """
            )


class AllianceDisbandedEvent(Event):
    """Logs an alliance being disbanded"""

    __slots__ = ("alliance",)

    alliance: Entity

    def __init__(self, alliance: Entity) -> None:
        super().__init__(alliance.world)
        self.alliance = alliance

    def get_description(self) -> str:
        return "{} has disbanded.".format(self.alliance.name_with_uid)

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    AllianceDisbandedEvent (
                        uid, alliance, timestamp
                    )
                VALUES
                    (?, ?, ?, ?, ?)
                """,
                (
                    self.uid,
                    self.alliance.uid,
                    self.timestamp,
                ),
            )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS AllianceDisbandedEvent;

                CREATE TABLE AllianceDisbandedEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    alliance INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (alliance) REFERENCES Alliance(uid)
                ) STRICT;
                """
            )


class LeaveAllianceEvent(Event):
    """Logs a family leaving their alliance."""

    __slots__ = ("alliance", "family", "family_head")

    alliance: Entity
    family: Entity
    family_head: Optional[Entity]

    def __init__(
        self, alliance: Entity, family: Entity, family_head: Optional[Entity]
    ) -> None:
        super().__init__(alliance.world)
        self.alliance = alliance
        self.family = family
        self.family_head = family_head
        if family_head is not None:
            self.logged_to = [family_head]

    def get_description(self) -> str:
        if self.family_head is None:
            return "The {} family left the {} alliance.".format(
                self.family.name_with_uid, self.alliance.name_with_uid
            )
        else:
            return "{} left the {} alliance.".format(
                self.family_head.name_with_uid,
                self.alliance.name_with_uid,
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    LeaveAllianceEvent (
                        uid, alliance, family, family_head, timestamp
                    )
                VALUES
                    (?, ?, ?, ?, ?)
                """,
                (
                    self.uid,
                    self.alliance.uid,
                    self.family.uid,
                    (self.family_head.uid if self.family_head is not None else None),
                    self.timestamp,
                ),
            )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS LeaveAllianceEvent;

                CREATE TABLE LeaveAllianceEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    alliance INT NOT NULL,
                    family INT NOT NULL,
                    family_head INT,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (alliance) REFERENCES Alliance(uid)
                ) STRICT;
                """
            )


class JoinAllianceEvent(Event):
    """Logs a character bringing their family into an alliance."""

    __slots__ = ("family_head", "family", "alliance")

    family_head: Entity
    family: Entity
    alliance: Entity

    def __init__(self, family_head: Entity, family: Entity, alliance: Entity) -> None:
        super().__init__(family_head.world)
        self.family_head = family_head
        self.family = family
        self.alliance = alliance
        self.logged_to = [family_head]

    def get_description(self) -> str:
        return "{} joined the {}.".format(
            self.family_head.name_with_uid,
            self.alliance.name_with_uid,
        )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    JoinAllianceEvent (
                        uid, alliance, family, family_head, timestamp
                    )
                VALUES
                    (?, ?, ?, ?, ?)
                """,
                (
                    self.uid,
                    self.alliance.uid,
                    self.family.uid,
                    self.family_head.uid,
                    self.timestamp,
                ),
            )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS JoinAllianceEvent;

                CREATE TABLE JoinAllianceEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    alliance INT NOT NULL,
                    family INT NOT NULL,
                    family_head INT,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (alliance) REFERENCES Alliance(uid)
                ) STRICT;
                """
            )


class GiveToTerritoriesEvent(Event):
    """Logs a character giving back to the small folk of a territory."""

    __slots__ = ("subject",)

    subject: Entity

    def __init__(self, subject: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.logged_to = [subject]

    def get_description(self) -> str:
        return "{} gave back to their territories.".format(self.subject.name_with_uid)

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS GiveToTerritoriesEvent;

                CREATE TABLE GiveToTerritoriesEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    GiveToTerritoriesEvent (uid, subject, timestamp)
                VALUES
                    (?, ?, ?);
                """,
                (self.uid, self.subject.uid, self.timestamp),
            )


class JoinCoupSchemeEvent(Event):
    """Logs a character joining someone's coup scheme."""

    __slots__ = ("subject", "scheme", "schemer")

    subject: Entity
    scheme: Entity
    schemer: Entity

    def __init__(self, subject: Entity, scheme: Entity, schemer: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.scheme = scheme
        self.schemer = schemer
        self.logged_to = [subject]

    def get_description(self) -> str:
        return "{} joined {}'s coup scheme.".format(
            self.subject.name_with_uid, self.schemer.name_with_uid
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS JoinCoupSchemeEvent;

                CREATE TABLE JoinCoupSchemeEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    scheme INT NOT NULL,
                    schemer INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid),
                    FOREIGN KEY (schemer) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    JoinCoupSchemeEvent (uid, subject, scheme, schemer, timestamp)
                VALUES
                    (?, ?, ?, ?, ?);
                """,
                (
                    self.uid,
                    self.subject.uid,
                    self.scheme.uid,
                    self.schemer.uid,
                    self.timestamp,
                ),
            )


class StartCoupSchemeEvent(Event):
    """Logs a character attempting to overthrow the current ruler."""

    __slots__ = ("subject", "ruler")

    subject: Entity
    ruler: Entity

    def __init__(self, subject: Entity, ruler: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.ruler = ruler
        self.logged_to = [subject]

    def get_description(self) -> str:
        return "{} started a scheme to overthrow {}.".format(
            self.subject.name_with_uid, self.ruler.name_with_uid
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS StartCoupSchemeEvent;

                CREATE TABLE StartCoupSchemeEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    ruler INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid),
                    FOREIGN KEY (ruler) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    StartCoupSchemeEvent (uid, subject, ruler, timestamp)
                VALUES
                    (?, ?, ?, ?);
                """,
                (
                    self.uid,
                    self.subject.uid,
                    self.ruler.uid,
                    self.timestamp,
                ),
            )


class RemovedFromPowerEvent(Event):
    """Logs when a family is removed from power over a territory."""

    __slots__ = ("subject", "territory")

    subject: Entity
    territory: Entity

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.territory = territory
        self.logged_to = [subject]


class StartWarSchemeEvent(Event):
    """Logs a character starting a war scheme."""

    __slots__ = ("subject", "opponent", "territory")

    subject: Entity
    opponent: Entity
    territory: Entity

    def __init__(self, subject: Entity, opponent: Entity, territory: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.opponent = opponent
        self.territory = territory
        self.logged_to = [subject, opponent]

    def get_description(self) -> str:
        return "{} started a war scheme against {} for the {} territory.".format(
            self.opponent.name_with_uid,
            self.subject.name_with_uid,
            self.territory.name_with_uid,
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS StartWarSchemeEvent;

                CREATE TABLE StartWarSchemeEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    opponent INT NOT NULL,
                    territory INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid),
                    FOREIGN KEY (opponent) REFERENCES Character(uid),
                    FOREIGN KEY (territory) REFERENCES Territory(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    StartWarSchemeEvent (uid, subject, opponent, territory, timestamp)
                VALUES
                    (?, ?, ?, ?, ?);
                """,
                (
                    self.uid,
                    self.subject.uid,
                    self.opponent.uid,
                    self.territory.uid,
                    self.timestamp,
                ),
            )


class DeclareWarEvent(Event):
    """Logs a character officially declaring war against another."""

    __slots__ = ("subject", "opponent", "territory")

    subject: Entity
    opponent: Entity
    territory: Entity

    def __init__(self, subject: Entity, opponent: Entity, territory: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.opponent = opponent
        self.territory = territory
        self.logged_to = [subject, opponent]

    def get_description(self) -> str:
        return "{} declared war on {} for the {} territory.".format(
            self.opponent.name_with_uid,
            self.subject.name_with_uid,
            self.territory.name_with_uid,
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS DeclareWarEvent;

                CREATE TABLE DeclareWarEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    opponent INT NOT NULL,
                    territory INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid),
                    FOREIGN KEY (opponent) REFERENCES Character(uid),
                    FOREIGN KEY (territory) REFERENCES Territory(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    DeclareWarEvent (uid, subject, opponent, territory, timestamp)
                VALUES
                    (?, ?, ?, ?, ?);
                """,
                (
                    self.uid,
                    self.subject.uid,
                    self.opponent.uid,
                    self.territory.uid,
                    self.timestamp,
                ),
            )


class QuellRevoltEvent(Event):
    """Logs a character quelling a revolt as head of the family."""

    __slots__ = ("subject", "territory")

    subject: Entity
    territory: Entity

    def __init__(self, subject: Entity, territory: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.territory = territory
        self.logged_to = [subject]

    def get_description(self) -> str:
        return "{} quelled the revolt in the {} territory".format(
            self.subject.name_with_uid, self.territory.name_with_uid
        )


class TaxTerritoriesEvent(Event):
    """Logs a character taxing a territory as head of the family."""

    __slots__ = ("subject",)

    def __init__(self, subject: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.logged_to = [subject]

    def get_description(self) -> str:
        return "{} levied an additional tax on their territories".format(
            self.subject.name_with_uid
        )


class RevoltEvent(Event):
    """Logs a territory revolting against a family."""

    __slots__ = ("territory", "family")

    territory: Entity
    family: Entity

    def __init__(self, territory: Entity, family: Entity) -> None:
        super().__init__(territory.world)
        self.territory = territory
        self.family = family

    def get_description(self) -> str:
        return "The {} territory is revolting against the {} family's control".format(
            self.territory.name_with_uid, self.family.name_with_uid
        )


class WarLostEvent(Event):
    """Logs a character losing a war."""

    __slots__ = ("subject", "opponent", "territory")

    subject: Entity
    opponent: Entity
    territory: Entity

    def __init__(self, subject: Entity, opponent: Entity, territory: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.opponent = opponent
        self.territory = territory
        self.logged_to = [subject]

    def get_description(self) -> str:
        return "{} was defeated by {} for the {} territory.".format(
            self.opponent.name_with_uid,
            self.subject.name_with_uid,
            self.territory.name_with_uid,
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS WarLostEvent;

                CREATE TABLE WarLostEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    opponent INT NOT NULL,
                    territory INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid),
                    FOREIGN KEY (opponent) REFERENCES Character(uid),
                    FOREIGN KEY (territory) REFERENCES Territory(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    WarLostEvent (uid, subject, opponent, territory, timestamp)
                VALUES
                    (?, ?, ?, ?, ?);
                """,
                (
                    self.uid,
                    self.subject.uid,
                    self.opponent.uid,
                    self.territory.uid,
                    self.timestamp,
                ),
            )


class WarWonEvent(Event):
    """Logs a character wining a war."""

    __slots__ = ("subject", "opponent", "territory")

    subject: Entity
    opponent: Entity
    territory: Entity

    def __init__(self, subject: Entity, opponent: Entity, territory: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.opponent = opponent
        self.territory = territory
        self.logged_to = [subject]

    def get_description(self) -> str:
        return "{} defeated {} for the {} territory.".format(
            self.subject.name_with_uid,
            self.opponent.name_with_uid,
            self.territory.name_with_uid,
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS WarWonEvent;

                CREATE TABLE WarWonEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    opponent INT NOT NULL,
                    territory INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid),
                    FOREIGN KEY (opponent) REFERENCES Character(uid),
                    FOREIGN KEY (territory) REFERENCES Territory(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    WarWonEvent (uid, subject, opponent, territory, timestamp)
                VALUES
                    (?, ?, ?, ?, ?);
                """,
                (
                    self.uid,
                    self.subject.uid,
                    self.opponent.uid,
                    self.territory.uid,
                    self.timestamp,
                ),
            )


class StartAllianceEvent(Event):
    """Logs when a character successfully starts a new alliance."""

    __slots__ = ("subject", "alliance")

    subject: Entity
    alliance: Entity

    def __init__(self, subject: Entity, alliance: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.alliance = alliance
        self.logged_to = [subject]

    def get_description(self) -> str:
        return "{} started a new alliance.".format(self.subject.name_with_uid)

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS StartAllianceEvent;

                CREATE TABLE StartAllianceEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    alliance INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid),
                    FOREIGN KEY (alliance) REFERENCES Alliance(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    StartAllianceEvent (uid, subject, alliance, timestamp)
                VALUES
                    (?, ?, ?, ?);
                """,
                (
                    self.uid,
                    self.subject.uid,
                    self.alliance.uid,
                    self.timestamp,
                ),
            )


class CoupSchemeDiscoveredEvent(Event):
    """Logs when a character's coup scheme is discovered."""

    __slots__ = ("subject", "schemer")

    subject: Entity
    schemer: Entity

    def __init__(self, subject: Entity, schemer: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.schemer = schemer
        self.logged_to = [subject, schemer]

    def get_description(self) -> str:
        return "{} discovered {}'s coup scheme.".format(
            self.subject.name_with_uid, self.schemer.name_with_uid
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS CoupSchemeDiscoveredEvent;

                CREATE TABLE CoupSchemeDiscoveredEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    schemer INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid),
                    FOREIGN KEY (schemer) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    CoupSchemeDiscoveredEvent (uid, subject, schemer, timestamp)
                VALUES
                    (?, ?, ?, ?);
                """,
                (
                    self.uid,
                    self.subject.uid,
                    self.schemer.uid,
                    self.timestamp,
                ),
            )


class SentenceToDeathEvent(Event):
    """Logs when a character is sentenced to death for a failed coup."""

    __slots__ = ("subject", "target", "reason")

    subject: Entity
    target: Entity
    reason: Optional[str]

    def __init__(
        self, subject: Entity, target: Entity, reason: Optional[str] = None
    ) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.target = target
        self.reason = reason
        self.logged_to = [subject, target]

    def get_description(self) -> str:
        return "{} sentenced {} to death for {}.".format(
            self.subject.name_with_uid, self.target.name_with_uid, self.reason
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS SentencedToDeathEvent;

                CREATE TABLE SentencedToDeathEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    target INT NOT NULL,
                    reason TEXT,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid),
                    FOREIGN KEY (target) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    SentencedToDeathEvent (uid, subject, target, reason, timestamp)
                VALUES
                    (?, ?, ?, ?, ?);
                """,
                (
                    self.uid,
                    self.subject.uid,
                    self.target.uid,
                    self.reason,
                    self.timestamp,
                ),
            )


class UsurpThroneEvent(Event):
    """Logs when a character usurps another for the thrown."""

    __slots__ = ("subject", "ruler")

    subject: Entity
    ruler: Entity

    def __init__(self, subject: Entity, ruler: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.ruler = ruler
        self.logged_to = [subject, ruler]

    def get_description(self) -> str:
        return "{} usurped the thrown from {}.".format(
            self.subject.name_with_uid, self.ruler.name_with_uid
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS UsurpThroneEvent;

                CREATE TABLE UsurpThroneEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    ruler INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid),
                    FOREIGN KEY (ruler) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    UsurpThroneEvent (uid, subject, ruler, timestamp)
                VALUES
                    (?, ?, ?, ?);
                """,
                (
                    self.uid,
                    self.subject.uid,
                    self.ruler.uid,
                    self.timestamp,
                ),
            )


class CheatOnSpouseEvent(Event):
    """Logs when a character cheats on their spouse."""

    __slots__ = ("subject", "spouse", "accomplice")

    subject: Entity
    spouse: Entity
    accomplice: Entity

    def __init__(self, subject: Entity, spouse: Entity, accomplice: Entity) -> None:
        super().__init__(subject.world)
        self.subject = subject
        self.spouse = spouse
        self.accomplice = accomplice
        self.logged_to = [subject]

    def get_description(self) -> str:
        return "{} cheated on {} with {}.".format(
            self.subject.name_with_uid,
            self.spouse.name_with_uid,
            self.accomplice.name_with_uid,
        )

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS CheatOnSpouseEvent;

                CREATE TABLE CheatOnSpouseEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    spouse INT NOT NULL,
                    accomplice INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid),
                    FOREIGN KEY (spouse) REFERENCES Character(uid),
                    FOREIGN KEY (accomplice) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    CheatOnSpouseEvent (uid, subject, spouse, accomplice, timestamp)
                VALUES
                    (?, ?, ?, ?, ?);
                """,
                (
                    self.uid,
                    self.subject.uid,
                    self.spouse.uid,
                    self.accomplice.uid,
                    self.timestamp,
                ),
            )


class SeizeTerritoryEvent(Event):
    """Logs a record of a family head taking control of a territory."""

    __slots__ = ("character", "family", "territory")

    character: Entity
    family: Entity
    territory: Entity

    def __init__(self, character: Entity, family: Entity, territory: Entity) -> None:
        super().__init__(character.world)
        self.character = character
        self.family = family
        self.territory = territory
        self.logged_to = [character]

    def get_description(self) -> str:
        return "{} took control of the {} territory.".format(
            self.character.name_with_uid, self.territory.name_with_uid
        )


class BecameRulerEvent(Event):
    """Event dispatched when a character becomes the ruler."""

    __slots__ = ("character",)

    character: Entity

    def __init__(self, character: Entity) -> None:
        super().__init__(character.world)
        self.character = character
        self.logged_to = [character]

    def get_description(self) -> str:
        return "{} became ruler.".format(self.character.name_with_uid)

    @staticmethod
    def configure_db_table(world: World) -> None:
        """Configure a SQLite table to hold events of this type."""
        with world.get_resource(SimDB) as db:
            db.executescript(
                """
                DROP TABLE IF EXISTS BecameRulerEvent;

                CREATE TABLE BecameRulerEvent (
                    uid INT NOT NULL PRIMARY KEY,
                    subject INT NOT NULL,
                    timestamp INT NOT NULL,
                    FOREIGN KEY (subject) REFERENCES Character(uid)
                ) STRICT;
                """
            )

    def log_to_db(self) -> None:
        with self.world.get_resource(SimDB) as db:
            db.execute(
                """
                INSERT INTO
                    BecameRulerEvent (uid, subject, timestamp)
                VALUES
                    (?, ?, ?);
                """,
                (
                    self.uid,
                    self.character.uid,
                    self.timestamp,
                ),
            )

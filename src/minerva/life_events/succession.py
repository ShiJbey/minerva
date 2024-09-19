"""Life Events Associated with Power Succession."""

from minerva.ecs import GameObject
from minerva.life_events.base_types import LifeEvent, LifeEventHistory
from minerva.sim_db import SimDB


class BecameFamilyHeadEvent(LifeEvent):
    """Event dispatched when a character becomes head of a family."""

    __slots__ = ("character", "family")

    character: GameObject
    family: GameObject

    def __init__(self, character: GameObject, family: GameObject) -> None:
        super().__init__(
            event_type="became-family-head",
            world=character.world,
            character=character,
            family=family,
        )
        self.character = character
        self.family = family

    def record_in_database(self, db: SimDB) -> None:
        """Record event within the database."""
        cur = db.db.cursor()
        cur.execute(
            """
            INSERT INTO life_events (event_id, event_type, timestamp, description)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.event_type,
                self.timestamp.to_iso_str(),
                self.get_description(),
            ),
        )
        cur.execute(
            """
            INSERT INTO became_family_head_events
            (event_id, character_id, family_id, timestamp)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.character.uid,
                self.family.uid,
                self.timestamp.to_iso_str(),
            ),
        )
        db.db.commit()

    def on_dispatch(self) -> None:
        self.character.dispatch_event(self)
        self.character.get_component(LifeEventHistory).history.append(self)
        self.record_in_database(self.world.resources.get_resource(SimDB))

    def get_description(self) -> str:
        return (
            f"{self.character.name} became the head of the {self.family.name} family."
        )


class BecameClanHeadEvent(LifeEvent):
    """Event dispatched when a character becomes head of a clan."""

    __slots__ = ("character", "clan")

    character: GameObject
    clan: GameObject

    def __init__(self, character: GameObject, clan: GameObject) -> None:
        super().__init__(
            event_type="became-clan-head",
            world=character.world,
            character=character,
            clan=clan,
        )
        self.character = character
        self.clan = clan

    def on_dispatch(self) -> None:
        self.character.dispatch_event(self)
        self.character.get_component(LifeEventHistory).history.append(self)

        db = self.world.resources.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO life_events (event_id, event_type, timestamp, description)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.event_type,
                self.timestamp.to_iso_str(),
                self.get_description(),
            ),
        )
        cur.execute(
            """
            INSERT INTO became_clan_head_events
            (event_id, character_id, clan_id, timestamp)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.character.uid,
                self.clan.uid,
                self.timestamp.to_iso_str(),
            ),
        )
        db.commit()

    def get_description(self) -> str:
        return f"{self.character.name} became the head of the {self.clan.name} clan."


class BecameEmperorEvent(LifeEvent):
    """Event dispatched when a character becomes emperor."""

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(
            event_type="became-emperor",
            world=character.world,
            character=character,
        )
        self.character = character

    def on_dispatch(self) -> None:
        self.character.dispatch_event(self)
        self.character.get_component(LifeEventHistory).history.append(self)

        db = self.world.resources.get_resource(SimDB).db
        cur = db.cursor()
        cur.execute(
            """
            INSERT INTO life_events (event_id, event_type, timestamp, description)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.event_type,
                self.timestamp.to_iso_str(),
                self.get_description(),
            ),
        )
        cur.execute(
            """
            INSERT INTO became_emperor_events
            (event_id, character_id, timestamp)
            VALUES (?, ?, ?);
            """,
            (
                self.event_id,
                self.character.uid,
                self.timestamp.to_iso_str(),
            ),
        )
        db.commit()

    def get_description(self) -> str:
        return f"{self.character.name} became emperor."


class FamilyRemovedFromPlay(LifeEvent):
    """Event dispatched when a family is removed from play."""

    __slots__ = ("family",)

    family: GameObject

    def __init__(self, family: GameObject) -> None:
        super().__init__(
            event_type="family-removed-from-play",
            world=family.world,
            family=family,
        )
        self.family = family

    def on_dispatch(self) -> None:
        pass

    def get_description(self) -> str:
        return f"The {self.family.name} family has been removed from play."


class ClanRemovedFromPlay(LifeEvent):
    """Event dispatched when a clan is removed from play."""

    __slots__ = ("clan",)

    clan: GameObject

    def __init__(self, clan: GameObject) -> None:
        super().__init__(
            event_type="clan-removed-from-play",
            world=clan.world,
            clan=clan,
        )
        self.clan = clan

    def on_dispatch(self) -> None:
        pass

    def get_description(self) -> str:
        return f"The {self.clan.name} clan has been removed from play."

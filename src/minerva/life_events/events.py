"""General Life Events."""

from minerva.ecs import GameObject
from minerva.life_events.base_types import LifeEvent, LifeEventHistory
from minerva.sim_db import SimDB


class MarriageEvent(LifeEvent):
    """Event dispatched when a character gets married."""

    __slots__ = ("character", "spouse")

    character: GameObject
    spouse: GameObject

    def __init__(self, character: GameObject, spouse: GameObject) -> None:
        super().__init__(
            event_type="marriage",
            world=character.world,
            character=character,
            spouse=spouse,
        )
        self.character = character
        self.spouse = spouse

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
            INSERT INTO marriage_events (event_id, character_id, spouse_id, timestamp)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.character.uid,
                self.spouse.uid,
                self.timestamp.to_iso_str(),
            ),
        )
        db.commit()

    def get_description(self) -> str:
        return f"{self.character.name_with_uid} married {self.spouse.name_with_uid}."


class PregnancyEvent(LifeEvent):
    """Event dispatched when a character gets pregnant."""

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(
            event_type="pregnancy",
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
            INSERT INTO pregnancy_events (event_id, character_id, timestamp)
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
        return f"{self.character.name_with_uid} became pregnant."


class GiveBirthEvent(LifeEvent):
    """Event dispatched when a character gives birth to another."""

    __slots__ = ("character", "child")

    character: GameObject
    child: GameObject

    def __init__(self, character: GameObject, child: GameObject) -> None:
        super().__init__(
            event_type="give-birth",
            world=character.world,
            character=character,
            child=child,
        )
        self.character = character
        self.child = child

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
            INSERT INTO give_birth_events (event_id, character_id, child_id, timestamp)
            VALUES (?, ?, ?, ?);
            """,
            (
                self.event_id,
                self.character.uid,
                self.child.uid,
                self.timestamp.to_iso_str(),
            ),
        )
        db.commit()

    def get_description(self) -> str:
        return (
            f"{self.character.name_with_uid} gave birth to {self.child.name_with_uid}."
        )


class BornEvent(LifeEvent):
    """Event dispatched when a character is born."""

    __slots__ = ("character",)

    character: GameObject

    def __init__(self, character: GameObject) -> None:
        super().__init__(
            event_type="born",
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
            INSERT INTO born_events (event_id, character_id, timestamp)
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
        return f"{self.character.name_with_uid} was born."


class TakeOverProvinceEvent(LifeEvent):
    """Event dispatched when a family head seizes power over a province."""

    __slots__ = ("character", "province", "family")

    character: GameObject
    province: GameObject
    family: GameObject

    def __init__(
        self, character: GameObject, province: GameObject, family: GameObject
    ) -> None:
        super().__init__(
            event_type="born",
            world=character.world,
            character=character,
            province=province,
            family=family,
        )
        self.character = character
        self.province = province
        self.family = family

    def on_dispatch(self) -> None:
        self.character.dispatch_event(self)
        self.character.get_component(LifeEventHistory).history.append(self)

        # db = self.world.resources.get_resource(SimDB).db
        # cur = db.cursor()
        # cur.execute(
        #     """
        #     INSERT INTO life_events (event_id, event_type, timestamp, description)
        #     VALUES (?, ?, ?, ?);
        #     """,
        #     (
        #         self.event_id,
        #         self.event_type,
        #         self.timestamp.to_iso_str(),
        #         self.get_description(),
        #     ),
        # )
        # cur.execute(
        #     """
        #     INSERT INTO born_events (event_id, character_id, timestamp)
        #     VALUES (?, ?, ?);
        #     """,
        #     (
        #         self.event_id,
        #         self.character.uid,
        #         self.timestamp.to_iso_str(),
        #     ),
        # )
        # db.commit()

    def get_description(self) -> str:
        return (
            f"{self.character.name_with_uid} took control of the "
            f"{self.province.name_with_uid} province for the "
            f"{self.family.name_with_uid} family."
        )

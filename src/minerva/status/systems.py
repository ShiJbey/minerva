"""Status Actions and Systems."""

from __future__ import annotations

from minerva.ecs import Active, Entity, System, World
from minerva.game_action import GameAction
from minerva.status.data import Status, StatusDatabase, StatusManager


class ApplyStatus(GameAction):
    """Apply a status to an entity."""

    __slots__ = ("target", "status_id")

    target: Entity
    status_id: str

    def __init__(self, target: Entity, status_id: str) -> None:
        super().__init__(target.world)
        self.target = target
        self.status_id = status_id

    def on_execute(self) -> None:
        status_db = self.world.get_resource(StatusDatabase)
        status = status_db.get_status(self.status_id)

        self.target.get_component(StatusManager).statuses.append(status)

        for effect in status.effects:
            effect.apply(self.target)


class RemoveStatus(GameAction):
    """Remove a status from an entity."""

    __slots__ = ("target", "status_id")

    target: Entity
    status_id: str

    def __init__(self, target: Entity, status_id: str) -> None:
        super().__init__(target.world)
        self.target = target
        self.status_id = status_id

    def on_execute(self) -> None:
        status_db = self.world.get_resource(StatusDatabase)
        status = status_db.get_status(self.status_id)

        status_manager = self.target.get_component(StatusManager)

        for status in status_manager.statuses:
            if status.status_id == self.status_id:
                for effect in status.effects:
                    effect.apply(self.target)

        status_manager.statuses = [
            s for s in status_manager.statuses if s.status_id != self.status_id
        ]


class StatusSystem(System):
    """Manages the update of statuses over time."""

    def on_update(self, world: World) -> None:
        for uid, (status_manager, _) in world.query_components((StatusManager, Active)):
            entity = world.get_entity(uid)
            expired_statuses: list[Status] = []
            for status in status_manager.statuses:
                if not status.has_duration:
                    continue

                if status.duration == 0:
                    expired_statuses.append(status)
                    continue

                status.duration -= 1

            # Remove all expired statuses
            for status in expired_statuses:
                RemoveStatus(entity, status.status_id).execute()

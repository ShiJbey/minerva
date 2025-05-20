"""Status Data and Data-Management classes."""

from typing import Optional

from minerva.ecs import Component
from minerva.traits.base_types import TraitEffect


class StatusData:
    """General data about a status."""

    __slots__ = (
        "status_id",
        "name",
        "duration",
        "has_duration",
        "effects",
    )

    status_id: str
    """A unique text ID for the status."""
    name: str
    """The name of the status to be displayed in UI."""
    duration: int
    """The number of simulation ticks the status lasts."""
    has_duration: bool
    """Should duration be considered for this (set if duration is < 0)."""
    effects: list[TraitEffect]
    """Effects applied when the status is attached."""

    def __init__(
        self,
        status_id: str,
        name: str,
        duration: int = -1,
        effects: Optional[list[TraitEffect]] = None,
    ) -> None:
        self.status_id = status_id
        self.name = name
        self.duration = duration
        self.has_duration = duration >= 0
        self.effects = effects if effects is not None else []

    def __hash__(self) -> int:
        return hash(self.status_id)

    def __str__(self) -> str:
        return self.name


class Status:
    """An instance of a status attached to an entity."""

    __slots__ = ("_status_data", "duration", "is_expired")

    _status_data: StatusData
    """Data about this status."""
    duration: int
    """The time remaining until this status is removed."""
    is_expired: bool
    """Is the status expired and should be removed."""

    def __init__(self, status_data: StatusData) -> None:
        self._status_data = status_data
        self.duration = status_data.duration
        self.is_expired = False

    @property
    def status_id(self) -> str:
        """The unique text ID of the status."""
        return self._status_data.status_id

    @property
    def name(self) -> str:
        """The name of the status as displayed in UI."""
        return self._status_data.name

    @property
    def effects(self) -> list[TraitEffect]:
        """The effects applied by the status."""
        return self._status_data.effects

    @property
    def has_duration(self) -> bool:
        """Does the status expire after a certain amount of time."""
        return self._status_data.has_duration


class StatusManager(Component):
    """Tracks all statuses attached to an entity."""

    __slots__ = ("statuses",)

    statuses: list[Status]

    def __init__(self) -> None:
        super().__init__()
        self.statuses = []


class StatusDatabase:
    """Manages collection of all StatusData objects for runtime lookup."""

    __slots__ = ("_statuses",)

    _statuses: dict[str, StatusData]
    """Map of status IDs to status data objects."""

    def __init__(self) -> None:
        self._statuses = {}

    def add_status_data(self, status_data: StatusData) -> None:
        """Add status data to database."""
        self._statuses[status_data.status_id] = status_data

    def get_status(self, status_id: str) -> Status:
        """Instantiate a status from the database."""
        return Status(self._statuses[status_id])

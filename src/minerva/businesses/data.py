"""Component and dataclasses used to model businesses and occupations."""

import pydantic

from minerva.content_selection import get_with_tags


class OccupationType(pydantic.BaseModel):
    """An occupation associated with character and businesses."""

    name: str
    prestige: int = 1
    spawn_frequency: int = 1
    tags: set[str] = pydantic.Field(default_factory=set)


class BusinessType(pydantic.BaseModel):
    """A business associated with a settlement."""

    name: str
    owner_type: str
    employee_types: dict[str, int] = pydantic.Field(default_factory=dict)
    spawn_frequency: int = 1
    tags: set[str] = pydantic.Field(default_factory=set)


class OccupationLibrary:
    """All the occupation types that can exist."""

    __slots__ = ("occupation_types",)

    occupation_types: dict[str, OccupationType]
    """A Lookup table of occupation types."""

    def __init__(self) -> None:
        self.occupation_types = {}

    def add_occupation_type(self, occupation_type: OccupationType) -> None:
        """Add a occupation type to the library."""
        self.occupation_types[occupation_type.name] = occupation_type

    def get_with_tags(self, *tags: str) -> list[OccupationType]:
        """Get occupation types with the given tags."""

        if len(tags) == 0:
            raise ValueError("No tags provided.")

        matches = get_with_tags(
            [(entry, entry.tags) for entry in self.occupation_types.values()], tags
        )

        return matches


class BusinessLibrary:
    """All the business types that can exist."""

    __slots__ = ("business_types",)

    business_types: dict[str, BusinessType]
    """A Lookup table of business types."""

    def __init__(self) -> None:
        self.business_types = {}

    def add_business_type(self, business_type: BusinessType) -> None:
        """Add a business type to the library."""
        self.business_types[business_type.name] = business_type

    def get_with_tags(self, *tags: str) -> list[BusinessType]:
        """Get business types with the given tags."""

        if len(tags) == 0:
            raise ValueError("No tags provided.")

        matches = get_with_tags(
            [(b, b.tags) for b in self.business_types.values()], tags
        )

        return matches

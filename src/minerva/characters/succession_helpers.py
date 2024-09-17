"""Helper functions for implementing power succession.

Succession in Minerva operates using depth charts like in NCAA25. A character's position
within the depth chart represents their distance from inheriting the thrown. The person
at the top of the depth chart is considered the next in line (heir) to inherit the
family/household when the current head is no longer in power.

The first iteration of this depth chart places living candidates in the following order:

1. Children in family by descending age (biological and non-biological)
2. Spouse
3. Siblings within the family by descending age

Not all character within the depth chart are eligible to take the thrown. For example,
someone's primary heir might still be a child, and therefor unfit to rule. We keep these
characters active within the depth chart so that we can track their depth when they
ascend to power.

"""

from __future__ import annotations

from typing import Iterator, Optional

import attrs

from minerva.characters.components import (
    Character,
    Dynasty,
    DynastyTracker,
    Emperor,
    LifeStage,
)
from minerva.datetime import SimDate
from minerva.ecs import GameObject, World
from minerva.sim_db import SimDB


@attrs.define
class DepthChartRow:
    """A row entry in a succession depth chart."""

    depth: int
    character_id: int
    is_eligible: bool


class SuccessionDepthChart:
    """A depth chart for the succession order of a character."""

    __slots__ = ("_rows", "_index")

    _rows: list[DepthChartRow]
    _index: dict[int, DepthChartRow]

    def __init__(self) -> None:
        self._rows = []
        self._index = {}

    def add_row(self, character: GameObject, is_eligible: bool = True) -> None:
        """Add a row to the chart."""
        if character.uid in self._index:
            raise ValueError(f"Duplicate depth chart entry for: {character.name}")

        row = DepthChartRow(
            depth=len(self._rows),
            character_id=character.uid,
            is_eligible=is_eligible,
        )

        self._rows.append(row)
        self._index[character.uid] = row

    def get_depth(self, character: GameObject) -> int:
        """Get the depth of a character in the chart."""
        if row_data := self._index.get(character.uid):
            return row_data.depth

        return -1

    def iter_rows(self) -> Iterator[DepthChartRow]:
        """Iterate rows of the chart."""
        return iter(self._rows)

    def __iter__(self) -> Iterator[DepthChartRow]:
        return iter(self._rows)


class SuccessionChartCache:
    """Singleton class that manages depth charts for all current family heads."""

    __slots__ = ("_charts",)

    _charts: dict[int, SuccessionDepthChart]

    def __init__(self) -> None:
        self._charts = {}

    def get_chart_for(
        self, character: GameObject, recalculate: bool = False
    ) -> SuccessionDepthChart:
        """Get the chart for the given character"""
        if character.uid in self._charts and not recalculate:
            return self._charts[character.uid]

        depth_chart = get_succession_depth_chart(character)
        self._charts[character.uid] = depth_chart

        return depth_chart

    def remove_chart_for(self, character: GameObject) -> bool:
        """Removes the depth chart for the given character."""

        if character.uid in self._charts:
            del self._charts[character.uid]
            return True

        return False


def get_succession_depth_chart(character: GameObject) -> SuccessionDepthChart:
    """Calculate the succession depth chart for the given character."""

    depth_chart = SuccessionDepthChart()

    character_component = character.get_component(Character)

    # Get all children in the same family
    child_list: list[tuple[GameObject, float, bool]] = []
    for child in character_component.children:
        child_character_component = child.get_component(Character)
        is_eligible = (
            child_character_component.life_stage >= LifeStage.ADOLESCENT
            and child_character_component.is_alive is True
        )
        if child_character_component.family == character_component.family:
            child_list.append((child, child_character_component.age, is_eligible))

    # Sort children by age
    child_list.sort(key=lambda e: e[1], reverse=True)

    # Add children to the chart
    for child, _, is_eligible in child_list:
        depth_chart.add_row(child, is_eligible)

    # Get the spouse
    if character_component.spouse is not None:
        depth_chart.add_row(character_component.spouse, is_eligible=True)

    # Get living siblings in the same family
    sibling_list: list[tuple[GameObject, float, bool]] = []
    for sibling in character_component.siblings:
        sibling_character_component = sibling.get_component(Character)
        is_eligible = (
            sibling_character_component.life_stage >= LifeStage.ADOLESCENT
            and sibling_character_component.is_alive is True
        )
        if sibling_character_component.family == character_component.family:
            sibling_list.append((sibling, sibling_character_component.age, is_eligible))

    # Sort siblings by age
    sibling_list.sort(key=lambda e: e[1], reverse=True)

    # Add siblings to the chart
    for sibling, _, is_eligible in sibling_list:
        depth_chart.add_row(sibling, is_eligible)

    return depth_chart


def set_current_ruler(world: World, character: Optional[GameObject]) -> None:
    """Set the character who is currently the ruler.

    Setting the ruler changes who is currently in charge and potentially
    what dynasty is currently active. Consecutive rulers from the same
    family constitute a single dynasty. IF the new ruler comes from a different
    family, a new dynasty starts.

    There may be times when there is no active dynasty.

    Parameters
    ----------
    character
        The next ruler.
    """
    db = world.resources.get_resource(SimDB).db
    cur = db.cursor()
    dynasty_tracker = world.resources.get_resource(DynastyTracker)
    current_date = world.resources.get_resource(SimDate)

    # Check if there is a current dynasty and that it has a current ruler. If it
    # does, remove the ruler/emperor component and update their ruler entry in the
    # database
    if dynasty_tracker.current_dynasty is not None:
        current_dynasty_component = dynasty_tracker.current_dynasty.get_component(
            Dynasty
        )

        # Remove the current ruler
        if current_dynasty_component.current_ruler is not None:
            current_dynasty_component.current_ruler.remove_component(Emperor)
            cur.execute(
                """
                UPDATE rulers
                SET end_date=?
                WHERE character_id=?;
                """,
                (
                    current_date.to_iso_str(),
                    current_dynasty_component.current_ruler.uid,
                ),
            )
            current_dynasty_component.previous_rulers.add(
                current_dynasty_component.current_ruler
            )
            current_dynasty_component.current_ruler = None

        # Nobody has been assigned as the next ruler end the dynasty
        if character is None:
            current_dynasty_component.ending_date = current_date

            cur.execute(
                """
                UPDATE dynasties
                SET
                end_date=?
                WHERE
                uid=?;
                """,
                (current_date.to_iso_str(), current_dynasty_component.gameobject.uid),
            )

            dynasty_tracker.previous_dynasties.add(dynasty_tracker.current_dynasty)
            dynasty_tracker.current_dynasty = None

        # Check if the new ruler is from the same family
        else:
            character_component = character.get_component(Character)
            if character_component.family != current_dynasty_component.family:
                current_dynasty_component.ending_date = current_date

                cur.execute(
                    """
                    UPDATE dynasties
                    SET
                    end_date=?
                    WHERE
                    uid=?;
                    """,
                    (
                        current_date.to_iso_str(),
                        current_dynasty_component.gameobject.uid,
                    ),
                )

                dynasty_tracker.previous_dynasties.add(dynasty_tracker.current_dynasty)
                dynasty_tracker.current_dynasty = None

    if character is not None:

        if dynasty_tracker.current_dynasty is not None:
            current_dynasty_component = dynasty_tracker.current_dynasty.get_component(
                Dynasty
            )

            current_dynasty_component.current_ruler = character
            last_ruler = dynasty_tracker.last_ruler
            dynasty_tracker.all_rulers.add(character)
            character.add_component(Emperor())

            cur.execute(
                """
                INSERT INTO rulers
                (
                    character_id,
                    dynasty_id,
                    start_date,
                    predecessor_id
                )
                VALUES (?, ?, ?, ?);
                """,
                (
                    character.uid,
                    current_dynasty_component.gameobject.uid,
                    current_date.to_iso_str(),
                    last_ruler,
                ),
            )
        else:
            _start_new_dynasty(character)

    db.commit()


def _start_new_dynasty(founding_character: GameObject) -> GameObject:
    """Start a new dynasty and return it."""
    world = founding_character.world

    current_date = world.resources.get_resource(SimDate)
    dynasty_tracker = world.resources.get_resource(DynastyTracker)

    if dynasty_tracker.current_dynasty is not None:
        raise RuntimeError("Cannot start new dynasty while another is active.")

    character_component = founding_character.get_component(Character)
    family = character_component.family
    assert family is not None, "Dynasty founder missing family"

    dynasty_obj = world.gameobjects.spawn_gameobject(
        components=[
            Dynasty(
                founder=founding_character,
                family=family,
                founding_date=world.resources.get_resource(SimDate).copy(),
            )
        ],
        name=f"The {character_component.surname} dynasty",
    )
    dynasty_component = dynasty_obj.get_component(Dynasty)

    dynasty_tracker.current_dynasty = dynasty_obj
    dynasty_component.current_ruler = founding_character
    dynasty_component.previous_dynasty = dynasty_tracker.last_dynasty
    founding_character.add_component(Emperor())
    dynasty_tracker.all_rulers.add(founding_character)

    previous_ruler: Optional[GameObject] = None
    if dynasty_component.previous_dynasty:
        previous_dynasty_comp = dynasty_component.previous_dynasty.get_component(
            Dynasty
        )
        previous_ruler = previous_dynasty_comp.last_ruler

    db = world.resources.get_resource(SimDB).db
    cur = db.cursor()
    cur.execute(
        """
        INSERT INTO dynasties
        (
            uid,
            family_id,
            founder_id,
            start_date,
            previous_dynasty_id
        )
        VALUES (?, ?, ?, ?, ?);
        """,
        (
            dynasty_obj.uid,
            dynasty_component.family.uid,
            founding_character.uid,
            current_date.to_iso_str(),
            dynasty_component.previous_dynasty,
        ),
    )
    cur.execute(
        """
        INSERT INTO rulers
        (
            character_id,
            dynasty_id,
            start_date,
            predecessor_id
        )
        VALUES (?, ?, ?, ?);
        """,
        (
            founding_character.uid,
            dynasty_obj.uid,
            current_date.to_iso_str(),
            previous_ruler,
        ),
    )

    return dynasty_obj

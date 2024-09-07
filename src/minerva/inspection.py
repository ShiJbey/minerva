"""Simulation inspection helper functions.

Tools and helper functions for inspecting simulations.

"""

from typing import Callable, Union

import tabulate

from minerva import __version__
from minerva.characters.components import Character, Family, Household, Pregnancy
from minerva.ecs import Active, GameObject, GameObjectNotFoundError
from minerva.life_events.base_types import EventHistory
from minerva.relationships.base_types import Relationship, RelationshipManager
from minerva.simulation import Simulation
from minerva.stats.base_types import StatManager
from minerva.stats.helpers import get_stat
from minerva.traits.base_types import TraitManager
from minerva.world_map.components import Settlement


def _sign(num: Union[int, float]) -> str:
    """Get the sign of a number."""
    return "-" if num < 0 else "+"


def _title_section(obj: GameObject) -> str:
    """Return string output for the section containing general GameObject data."""

    name_line = f"|| {obj.name} ||"
    frame_top_bottom = "=" * len(name_line)

    output = [
        frame_top_bottom,
        name_line,
        frame_top_bottom,
        "",
        f"Active: {obj.is_active}",
        f"Name: {obj.name}",
    ]

    return "\n".join(output)


def _settlement_section(obj: GameObject) -> str:
    """Return string output for a section focuses on settlement data."""
    settlement = obj.try_component(Settlement)

    if settlement is None:
        return ""

    output = [
        "=== Settlement ===",
        "",
        f"Name: {settlement.name!r}",
    ]

    # Add controlling family information
    if settlement.controlling_family:
        output.append(
            f"Controlling Family: {settlement.controlling_family.name_with_uid}"
        )
    else:
        output.append("Controlling Family: N/A")

    # Add business types
    output.append(f"Business Types: {', '.join(settlement.business_types)}")

    # Add neighbors
    output.append(
        f"Neighboring Settlements: {','.join(s.name_with_uid for s in settlement.neighbors)}"
    )

    # Add families
    output.append(
        f"Resident Families: {','.join(f.name_with_uid for f in settlement.families)}"
    )

    # Add Political Influeces:
    output.append("Political Influences:")

    output += tabulate.tabulate(
        [
            (
                family.name_with_uid,
                influence,
            )
            for family, influence in settlement.political_influence.items()
        ],
        headers=("Family", "Influence"),
    )

    return "\n".join(output)


def _character_section(obj: GameObject) -> str:
    """Print information about a character."""
    character = obj.try_component(Character)

    if character is None:
        return ""

    output = [
        "=== Character ===",
        "",
        f"Name: {character.full_name!r}",
        f"Age: {character.age} ({character.life_stage.name})",
        f"Sex: {character.sex.name}",
        f"Species: {character.species.name}",
    ]

    return "\n".join(output)


def _relationship_section(obj: GameObject) -> str:
    """Print information about a relationship."""

    relationship = obj.try_component(Relationship)

    if relationship is None:
        return ""

    output = "=== Relationship ===\n"
    output += "\n"
    output += f"Owner: {relationship.owner.name}\n"
    output += f"Target: {relationship.target.name}\n"

    return output


def _household_section(obj: GameObject) -> str:
    """Print information about a household."""
    household = obj.try_component(Household)

    if household is None:
        return ""

    output: list[str] = [
        "=== Household ===",
        "",
        f"Head of Household: {household.head.name if household.head else 'N/A'}",
    ]

    if household.members:
        output.append(f"Members: (Total {len(household.members)})")
        for member in household.members:
            output.append(f"\t- {member.name}")
    else:
        output.append("Members: N/A")

    return "\n".join(output)


def _pregnancy_section(obj: GameObject) -> str:
    """Print information about a pregnancy component."""

    pregnancy = obj.try_component(Pregnancy)

    if pregnancy is None:
        return ""

    assumed_father_name = (
        pregnancy.assumed_father.name if pregnancy.assumed_father else "N/A"
    )
    actual_father_name = pregnancy.actual_father.name
    conception_date = str(pregnancy.conception_date)
    due_date = str(pregnancy.due_date)

    output = [
        "=== Pregnant ===",
        "",
        f"Assumed Father: {assumed_father_name}",
        f"Actual Father: {actual_father_name}",
        f"Conception Date: {conception_date}",
        f"Due Date: {due_date}",
    ]

    return "\n".join(output)


def _get_traits_table(obj: GameObject) -> str:
    """Generate a string table for a Traits component."""
    if not obj.has_component(TraitManager):
        return ""

    traits = obj.get_component(TraitManager)

    output = "=== Traits ===\n\n"

    output += tabulate.tabulate(
        [
            (
                entry.name,
                entry.description,
            )
            for entry in traits.traits.values()
        ],
        headers=("Name", "Description"),
    )

    return output


def _get_personal_history_table(obj: GameObject) -> str:
    """Generate a string table for a PersonalEventHistory component."""
    history = obj.try_component(EventHistory)

    if history is None:
        return ""

    event_data: list[tuple[str, str]] = [
        (str(event.timestamp), str(event)) for event in history.history
    ]

    output = "=== Event History ===\n\n"

    output += tabulate.tabulate(
        event_data,
        headers=("Timestamp", "Description"),
    )

    return output


def _get_relationships_table(obj: GameObject) -> str:
    relationships = obj.try_component(RelationshipManager)

    if relationships is None:
        return ""

    relationship_data: list[tuple[bool, int, str, str, str, str]] = []

    for target, relationship in relationships.outgoing.items():
        reputation = get_stat(relationship, "Reputation")
        romance = get_stat(relationship, "Romance")
        traits = ", ".join(
            t.name for t in relationship.get_component(TraitManager).traits.values()
        )
        rep_base = int(reputation.base_value)
        rom_base = int(romance.base_value)
        rep_boost = int(reputation.value - reputation.base_value)
        rom_boost = int(romance.value - romance.base_value)

        relationship_data.append(
            (
                relationship.has_component(Active),
                relationship.uid,
                target.name,
                f"{rep_base}[{_sign(rep_boost)}{abs(rep_boost)}]",
                f"{rom_base}[{_sign(rom_boost)}{abs(rom_boost)}]",
                traits,
            )
        )

    output = "=== Relationships ===\n\n"

    output += tabulate.tabulate(
        relationship_data,
        headers=(
            "Active",
            "UID",
            "Target",
            "Reputation",
            "Romance",
            "Traits",
        ),
    )

    return output


def _get_stats_table(obj: GameObject) -> str:
    """Generate a table for stats."""
    stats = obj.try_component(StatManager)

    if stats is None:
        return ""

    stats_table_data: list[tuple[str, str, str, str]] = []

    for stat_component in stats.stats.values():
        if stat_component.max_value is not None or stat_component.min_value is not None:
            min_val, max_val = stat_component.min_value, stat_component.max_value
        else:
            min_val, max_val = "N/A", "N/A"

        stat = stat_component
        boost = int(stat.value - stat.base_value)

        if stat.is_discrete:
            value_label = f"{int(stat.base_value)}[{_sign(boost)}{abs(boost)}]"
        else:
            value_label = f"{stat.base_value:.3f}[{_sign(boost)}{abs(boost)}]"

        stats_table_data.append(
            (stat_component.stat_name, value_label, str(min_val), str(max_val))
        )

    output = "=== Stats ===\n\n"

    output += tabulate.tabulate(
        stats_table_data,
        headers=("Stat", "Base Value[boost]", "Min", "Max"),
        numalign="left",
    )

    return output


_obj_inspector_sections: list[tuple[str, Callable[[GameObject], str]]] = [
    ("title", _title_section),
    ("settlement", _settlement_section),
    ("relationship", _relationship_section),
    ("character", _character_section),
    ("household", _household_section),
    ("stats", _get_stats_table),
    ("traits", _get_traits_table),
    ("pregnancy", _pregnancy_section),
    ("relationships", _get_relationships_table),
    ("personal_history", _get_personal_history_table),
]
"""Static data containing functions that print various inspector sections."""


def add_inspector_section_fn(
    section_name: str, section_fn: Callable[[GameObject], str], after: str = ""
) -> None:
    """Add a function that generates a section of inspector output.

    Parameters
    ----------
    section_name
        The name of the section (used internally for ordering sections)
    section_fn
        A callable that prints the output of the section
    after
        The name of the section that this section should follow (defaults to "")
    """
    if after == "":
        _obj_inspector_sections.append((section_name, section_fn))
        return

    index = 0
    while index < len(_obj_inspector_sections):
        if _obj_inspector_sections[index][0] == after:
            break
        index += 1

    _obj_inspector_sections.insert(index + 1, (section_name, section_fn))


class SimulationInspector:
    """A helper class for printing various simulation info to the terminal."""

    __slots__ = ("sim",)

    sim: Simulation

    def __init__(self, sim: Simulation) -> None:
        self.sim = sim

    def print_status(self) -> None:
        """Print the current status of the simulation."""

        output = ""
        output += "Simulation Status\n"
        output += "=================\n"
        output += "\n"
        output += f"World seed: {self.sim.config.seed}\n"
        output += (
            f"World date: month {self.sim.date.month} of year {self.sim.date.year}\n"
        )
        output += f"Simulation Version: {__version__}\n"

        print(output)

        self.list_settlements()
        self.list_families()

    def inspect(self, obj: Union[int, GameObject]) -> None:
        """Print information about a GameObject.

        Parameters
        ----------
        sim
            A simulation instance.
        obj
            The GameObject instance or ID to inspect.
        """
        if isinstance(obj, int):
            try:
                obj_ref = self.sim.world.gameobjects.get_gameobject(obj)
            except GameObjectNotFoundError:
                print(f"No GameObject exists with the ID: {obj}.")
                return
        else:
            obj_ref = obj

        section_output: list[str] = []

        for _, section_fn in _obj_inspector_sections:
            section_str = section_fn(obj_ref)
            if section_str:
                section_output.append(section_str)

        combined_output = "\n\n".join(section_output)

        print(combined_output)

    def list_settlements(self) -> None:
        """Print the list of settlements in the simulation."""
        settlements = [
            (uid, settlement.name)
            for uid, (settlement, _) in self.sim.world.get_components(
                (Settlement, Active)
            )
        ]

        table = tabulate.tabulate(settlements, headers=["UID", "Name"])

        # Display as a table the object ID, Display Name, Description
        output = "=== Settlements ===\n"
        output += table
        output += "\n"

        print(output)

    def list_characters(self, inactive_ok: bool = False) -> None:
        """Print a list of characters from the simulation."""
        if inactive_ok:
            characters = [
                (
                    uid,
                    character.full_name,
                    int(character.age),
                    str(character.sex.name),
                    str(character.species.name),
                )
                for uid, (character,) in self.sim.world.get_components((Character,))
            ]
        else:
            characters = [
                (
                    uid,
                    character.full_name,
                    int(character.age),
                    str(character.sex.name),
                    str(character.species.name),
                )
                for uid, (character, _) in self.sim.world.get_components(
                    (Character, Active)
                )
            ]

        table = tabulate.tabulate(
            characters, headers=["UID", "Name", "Age", "Sex", "Species"]
        )

        # Display as a table the object ID, Display Name, Description
        output = "=== Characters ===\n"
        output += table
        output += "\n"

        print(output)

    def list_families(self, inactive_ok: bool = False) -> None:
        """Print all the families in the simulation."""

        family_info: list[tuple[int, str, str, str, str]] = []

        if inactive_ok:
            family_info = [
                (
                    uid,
                    family.name,
                    family.head.name_with_uid if family.head else "N/A",
                    family.clan.name_with_uid if family.clan else "N/A",
                    family.home_base.name_with_uid if family.home_base else "N/A",
                )
                for uid, (family,) in self.sim.world.get_components((Family,))
            ]
        else:
            family_info = [
                (
                    uid,
                    family.name,
                    family.head.name_with_uid if family.head else "N/A",
                    family.clan.name_with_uid if family.clan else "N/A",
                    family.home_base.name_with_uid if family.home_base else "N/A",
                )
                for uid, (family, _) in self.sim.world.get_components((Family, Active))
            ]

        table = tabulate.tabulate(
            family_info, headers=["UID", "Name", "Head", "Clan", "Home Base"]
        )

        output = "=== Families ===\n"
        output += table
        output += "\n"

        print(output)

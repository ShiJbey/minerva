"""Simulation inspection helper functions.

Tools and helper functions for inspecting simulations.

"""

from typing import Callable, Union

import tabulate

from minerva import __version__
from minerva.characters.components import (
    Character,
    Dynasty,
    DynastyTracker,
    Emperor,
    Family,
    FamilyRoleFlags,
    HeadOfFamily,
    Pregnancy,
)
from minerva.ecs import Active, GameObject, GameObjectNotFoundError
from minerva.life_events.base_types import LifeEventHistory
from minerva.relationships.base_types import (
    Relationship,
    RelationshipManager,
    Reputation,
    Romance,
)
from minerva.simulation import Simulation
from minerva.traits.base_types import TraitManager
from minerva.world_map.components import Settlement


def _sign(num: Union[int, float]) -> str:
    """Get the sign of a number."""
    return "-" if num < 0 else "+"


def _title_section(obj: GameObject) -> str:
    """Return string output for the section containing general GameObject data."""

    name_line = f"|| {obj.name_with_uid} ||"
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

    # Add neighbors
    output.append(
        f"Neighboring Settlements: {','.join(s.name_with_uid for s in settlement.neighbors)}"
    )

    # Add families
    output.append(
        f"Resident Families: {','.join(f.name_with_uid for f in settlement.families)}"
    )

    # Add Political Influences:
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

    mother = character.mother.name_with_uid if character.mother else "N/A"
    father = character.father.name_with_uid if character.father else "N/A"
    spouse = character.spouse.name_with_uid if character.spouse else "N/A"
    lover = character.lover.name_with_uid if character.lover else "N/A"
    heir = character.heir.name_with_uid if character.heir else "N/A"
    heir_to = character.heir_to.name_with_uid if character.heir_to else "N/A"

    biological_father = (
        character.biological_father.name_with_uid
        if character.biological_father
        else "N/A"
    )
    family = character.family.name_with_uid if character.family else "N/A"
    birth_family = (
        character.birth_family.name_with_uid if character.birth_family else "N/A"
    )
    siblings = ", ".join(s.name_with_uid for s in character.siblings)
    children = ", ".join(s.name_with_uid for s in character.children)
    family_roles = ", ".join(
        str(r.name) for r in FamilyRoleFlags if r in character.family_roles
    )

    title_list: list[str] = []

    if obj.has_component(Emperor):
        title_list.append("Emperor")

    if head_of_family_comp := obj.try_component(HeadOfFamily):
        title_list.append(f"Head of {head_of_family_comp.family.name_with_uid} family")

    titles = ", ".join(title_list)

    output = [
        "=== Character ===",
        "",
        f"First Name: {character.first_name}",
        f"Surname: {character.surname}",
        f"Surname at Birth: {character.birth_surname}",
        f"Age: {int(character.age)} ({character.life_stage.name})",
        f"Is Alive: {character.is_alive}",
        f"Titles: {titles}",
        f"Birth Date: {character.birth_date}",
        f"Death Date: {character.death_date}",
        f"Sex: {character.sex.name}",
        f"Species: {character.species.name}",
        f"Sexual Orientation: {character.sexual_orientation.name}",
        f"Mother: {mother}",
        f"Father: {father}",
        f"Biological Father: {biological_father}",
        f"Family: {family}",
        f"Birth Family: {birth_family}",
        f"Siblings: {siblings}",
        f"Children: {children}",
        f"Spouse: {spouse}",
        f"Lover: {lover}",
        f"Heir: {heir}",
        f"Heir To: {heir_to}",
        f"Family Roles: {family_roles}",
        f"Influence Points: {int(character.influence_points)}",
    ]

    return "\n".join(output)


def _family_section(obj: GameObject) -> str:
    """Print information about a family component."""
    family_component = obj.try_component(Family)

    if not family_component:
        return ""

    parent_family = (
        family_component.parent_family.name_with_uid
        if family_component.parent_family
        else "None"
    )

    branch_families = ", ".join(
        f.name_with_uid for f in family_component.branch_families
    )

    head = family_component.head.name_with_uid if family_component.head else "None"

    former_heads = ", ".join(h.name_with_uid for h in family_component.former_heads)

    active_members = ", ".join(m.name_with_uid for m in family_component.active_members)

    former_members = ", ".join(m.name_with_uid for m in family_component.former_members)

    alliance = (
        family_component.alliance.name_with_uid if family_component.alliance else "None"
    )

    home_base = (
        family_component.home_base.name_with_uid
        if family_component.home_base
        else "None"
    )

    territories = ", ".join(t.name_with_uid for t in family_component.territories)

    warriors = ", ".join(w.name_with_uid for w in family_component.warriors)

    advisors = ", ".join(a.name_with_uid for a in family_component.advisors)

    output: list[str] = [
        "=== Family ===",
        "",
        f"Name: {family_component.name}",
        f"Parent Family: {parent_family}",
        f"Branch Families: {branch_families}",
        f"Head: {head}",
        f"Former Heads: {former_heads}",
        f"Active Members: {active_members}",
        f"Former Members: {former_members}",
        f"Alliance: {alliance}",
        f"Home Base: {home_base}",
        f"Territories: {territories}",
        f"Warriors: {warriors}",
        f"Advisors: {advisors}",
        "",
    ]

    return "\n".join(output)


def _dynasty_section(obj: GameObject) -> str:
    """Print information about a dynasty component."""

    dynasty_component = obj.try_component(Dynasty)

    if dynasty_component is None:
        return ""

    output: list[str] = [
        "=== Dynasty ===",
        "",
    ]

    current_ruler = (
        dynasty_component.current_ruler.name_with_uid
        if dynasty_component.current_ruler
        else "None"
    )

    previous_rulers = ", ".join(
        r.name_with_uid for r in dynasty_component.previous_rulers
    )

    previous_dynasty = (
        dynasty_component.previous_dynasty.name_with_uid
        if dynasty_component.previous_dynasty
        else "None"
    )

    output.append(f"Current Ruler: {current_ruler}")
    output.append(f"Founder: {dynasty_component.founder.name_with_uid}")
    output.append(f"Family: {dynasty_component.family.name_with_uid}")
    output.append(f"Founding Date: {dynasty_component.founding_date}")
    output.append(f"Ending Date: {dynasty_component.ending_date}")
    output.append(f"Previous Rulers: {previous_rulers}")
    output.append(f"Previous Dynasty: {previous_dynasty}")

    output.append("")

    return "\n".join(output)


def _relationship_section(obj: GameObject) -> str:
    """Print information about a relationship."""

    relationship = obj.try_component(Relationship)

    if relationship is None:
        return ""

    output = "=== Relationship ===\n"
    output += "\n"
    output += f"Owner: {relationship.owner.name_with_uid}\n"
    output += f"Target: {relationship.target.name_with_uid}\n"

    return output


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
    life_event_history = obj.try_component(LifeEventHistory)

    if life_event_history is None:
        return ""

    event_data: list[tuple[str, str]] = [
        (str(event.timestamp), event.get_description())
        for event in life_event_history.history
    ]

    output = "=== Event History ===\n\n"

    output += tabulate.tabulate(
        event_data,
        headers=("Timestamp", "Description"),
    )

    output += "\n"

    return output


def _get_relationships_table(obj: GameObject) -> str:
    relationships = obj.try_component(RelationshipManager)

    if relationships is None:
        return ""

    relationship_data: list[tuple[bool, int, str, str, str, str]] = []

    for target, relationship in relationships.outgoing_relationships.items():
        reputation = relationship.get_component(Reputation)
        romance = relationship.get_component(Romance)
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


_obj_inspector_sections: list[tuple[str, Callable[[GameObject], str]]] = [
    ("title", _title_section),
    ("settlement", _settlement_section),
    ("relationship", _relationship_section),
    ("character", _character_section),
    ("family", _family_section),
    ("dynasty", _dynasty_section),
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

        self.list_dynasties()
        self.list_settlements()
        self.list_families()

    def inspect(self, obj: Union[int, GameObject]) -> None:
        """Print information about a GameObject.

        Parameters
        ----------
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

    def list_dynasties(self) -> None:
        """Print information about the current dynasty."""
        dynasty_tracker = self.sim.world.resources.get_resource(DynastyTracker)

        output: list[str] = [
            "=== Current Dynasty ===",
            "",
        ]

        if dynasty_tracker.current_dynasty is None:
            output.append("No Current Dynasty")

        else:
            dynasty_component = dynasty_tracker.current_dynasty.get_component(Dynasty)

            current_ruler = (
                dynasty_component.current_ruler.name_with_uid
                if dynasty_component.current_ruler
                else "None"
            )

            previous_rulers = ", ".join(
                r.name_with_uid for r in dynasty_component.previous_rulers
            )

            previous_dynasty = (
                dynasty_component.previous_dynasty.name_with_uid
                if dynasty_component.previous_dynasty
                else "None"
            )

            output.append(f"Current Ruler: {current_ruler}")
            output.append(f"Founder: {dynasty_component.founder.name_with_uid}")
            output.append(f"Family: {dynasty_component.family.name_with_uid}")
            output.append(f"Founding Date: {dynasty_component.founding_date}")
            output.append(f"Previous Rulers: {previous_rulers}")
            output.append(f"Previous Dynasty: {previous_dynasty}")

        output.append("")
        output.append("=== Previous Dynasties ===")
        output.append("")

        dynasties = [
            (
                uid,
                dynasty.family.name_with_uid,
                dynasty.founding_date,
                dynasty.ending_date,
            )
            for uid, (dynasty,) in self.sim.world.get_components((Dynasty,))
            if dynasty.ending_date
        ]

        table = tabulate.tabulate(
            dynasties, headers=["UID", "Family", "Start Date", "End Date"]
        )

        output.append(table)
        output.append("")
        print("\n".join(output))

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
        output += "\n"
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
        output += "\n"
        output += table
        output += "\n"

        print(output)

    def list_families(self, inactive_ok: bool = False) -> None:
        """Print all the families in the simulation."""

        family_info: list[tuple[int, str, str, str]] = []

        if inactive_ok:
            family_info = [
                (
                    uid,
                    family.name,
                    family.head.name_with_uid if family.head else "N/A",
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
                    family.home_base.name_with_uid if family.home_base else "N/A",
                )
                for uid, (family, _) in self.sim.world.get_components((Family, Active))
            ]

        table = tabulate.tabulate(
            family_info, headers=["UID", "Name", "Head", "Home Base"]
        )

        output = "=== Families ===\n"
        output += "\n"
        output += table
        output += "\n"

        print(output)

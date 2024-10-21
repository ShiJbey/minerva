"""Simulation inspection helper functions.

Tools and helper functions for inspecting simulations.

"""

# from typing import Union

import rich.console
import rich.markdown
import rich.panel
import rich.table

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
from minerva.characters.succession_helpers import get_current_ruler
from minerva.characters.war_data import Alliance, War
from minerva.ecs import Active
from minerva.life_events.base_types import LifeEventHistory

# from minerva.relationships.base_types import Attraction, Opinion, RelationshipManager
from minerva.simulation import Simulation
from minerva.traits.base_types import TraitManager
from minerva.world_map.components import Territory

# def _sign(num: Union[int, float]) -> str:
#     """Get the sign of a number."""
#     return "-" if num < 0 else "+"


class SimulationInspector:
    """A helper class for printing various simulation info to the terminal."""

    __slots__ = ("sim",)

    sim: Simulation

    def __init__(self, sim: Simulation) -> None:
        self.sim = sim

    def print_status(self) -> None:
        """Print the current status of the simulation."""

        total_characters = len(self.sim.world.get_components((Character, Active)))
        total_families = len(self.sim.world.get_components((Family, Active)))
        total_territories = len(self.sim.world.get_components((Territory, Active)))
        total_wars = len(self.sim.world.get_components((War, Active)))
        total_alliances = len(self.sim.world.get_components((Alliance, Active)))
        current_ruler = get_current_ruler(self.sim.world)
        current_ruler_name = current_ruler.name_with_uid if current_ruler else "None"

        console = rich.console.Console()

        status_markdown_text: str = (
            "# Simulation Status\n"
            "\n"
            f"**World seed:** {self.sim.config.seed}\n\n"
            f"**World Date:** {self.sim.date.to_iso_str()}\n\n"
            f"**Simulation Version:** {__version__}\n\n"
            f"**Num Active Families:** {total_families}\n\n"
            f"**Num Active Characters:** {total_characters}\n\n"
            f"**Current Ruler:** {current_ruler_name}\n\n"
            f"**Num Active Territories:** {total_territories}\n\n"
            f"**Num Active Wars:** {total_wars}\n\n"
            f"**Num Active Alliances:** {total_alliances}\n\n"
            "\n"
        )

        status_markdown = rich.markdown.Markdown(status_markdown_text)

        panel = rich.panel.Panel(status_markdown)

        console.print(panel)

    def inspect_character(self, character_id: int) -> None:
        """Print information about a character to the console."""
        character = self.sim.world.gameobjects.get_gameobject(character_id)

        character_component = character.get_component(Character)

        mother = (
            character_component.mother.name_with_uid
            if character_component.mother
            else "None"
        )
        father = (
            character_component.father.name_with_uid
            if character_component.father
            else "None"
        )
        spouse = (
            character_component.spouse.name_with_uid
            if character_component.spouse
            else "None"
        )
        lover = (
            character_component.lover.name_with_uid
            if character_component.lover
            else "None"
        )
        heir = (
            character_component.heir.name_with_uid
            if character_component.heir
            else "None"
        )
        heir_to = (
            character_component.heir_to.name_with_uid
            if character_component.heir_to
            else "None"
        )

        biological_father = (
            character_component.biological_father.name_with_uid
            if character_component.biological_father
            else "None"
        )
        family = (
            character_component.family.name_with_uid
            if character_component.family
            else "None"
        )
        birth_family = (
            character_component.birth_family.name_with_uid
            if character_component.birth_family
            else "None"
        )
        siblings = ", ".join(s.name_with_uid for s in character_component.siblings)
        children = ", ".join(s.name_with_uid for s in character_component.children)
        family_roles = ", ".join(
            str(r.name)
            for r in FamilyRoleFlags
            if r in character_component.family_roles
        )

        title_list: list[str] = []

        if character.has_component(Emperor):
            title_list.append("Emperor")

        if head_of_family_comp := character.try_component(HeadOfFamily):
            title_list.append(
                f"Head of {head_of_family_comp.family.name_with_uid} family"
            )

        titles = ", ".join(title_list)

        output = [
            f"# [Character] {character.name_with_uid}\n",
            "\n",
            f"First Name: {character_component.first_name}\n",
            f"Surname: {character_component.surname}\n",
            f"Surname at Birth: {character_component.birth_surname}\n",
            f"Age: {int(character_component.age)} ({character_component.life_stage.name})\n",
            f"Is Alive: {character_component.is_alive}\n",
            f"Titles: {titles}\n",
            f"Birth Date: {character_component.birth_date}\n",
            f"Death Date: {character_component.death_date}\n",
            f"Sex: {character_component.sex.name}\n",
            f"Species: {character_component.species.name}\n",
            f"Sexual Orientation: {character_component.sexual_orientation.name}\n",
            f"Mother: {mother}\n",
            f"Father: {father}\n",
            f"Biological Father: {biological_father}\n",
            f"Family: {family}\n",
            f"Birth Family: {birth_family}\n",
            f"Siblings: {siblings}\n",
            f"Children: {children}\n",
            f"Spouse: {spouse}\n",
            f"Lover: {lover}\n",
            f"Heir: {heir}\n",
            f"Heir To: {heir_to}\n",
            f"Family Roles: {family_roles}\n",
            f"Influence Points: {int(character_component.influence_points)}\n",
            f"Is Pregnant: {character.has_component(Pregnancy)}\n",
        ]

        console = rich.console.Console()
        markdown_obj = rich.markdown.Markdown("\n".join(output))
        console.print("[bold red]alert![/bold red] Something happened")
        console.print(markdown_obj)
        console.print("===\n")

        traits = character.get_component(TraitManager)
        trait_table = rich.table.Table(
            "Name", "Description", title="Traits", title_justify="left"
        )
        for entry in traits.traits.values():
            trait_table.add_row(
                entry.name, entry.description if entry.description else "None"
            )
        console.print(trait_table)
        console.print("===\n")

        # relationships = character.get_component(RelationshipManager)

        # relationship_table = rich.table.Table(
        #     "Active",
        #     "Target",
        #     "Opinion",
        #     "Attraction",
        #     "Traits",
        #     title="Relationships",
        #     title_justify="left",
        # )

        # for target, relationship in relationships.outgoing_relationships.items():
        #     opinion = relationship.get_component(Opinion)
        #     attraction = relationship.get_component(Attraction)

        #     traits = ", ".join(
        #         t.name for t in relationship.get_component(TraitManager).traits.values()
        #     )

        #     op_base = int(opinion.base_value)
        #     atr_base = int(attraction.base_value)
        #     op_boost = int(opinion.value - opinion.base_value)
        #     atr_boost = int(attraction.value - attraction.base_value)

        #     relationship_table.add_row(
        #         str(relationship.has_component(Active)),
        #         target.name_with_uid,
        #         f"{op_base}[{_sign(op_boost)}{abs(op_boost)}]",
        #         f"{atr_base}[{_sign(atr_boost)}{abs(atr_boost)}]",
        #         traits,
        #     )

        # console.print(relationship_table)
        # console.print("===\n")

        life_event_history = character.get_component(LifeEventHistory)

        life_event_table = rich.table.Table(
            "Timestamp", "Description", title="Life Events", title_justify="left"
        )
        for event in life_event_history.history:
            life_event_table.add_row(str(event.timestamp), event.get_description())

        console.print(life_event_table)

    def inspect_family(self, family_id: int) -> None:
        """Print information about a family."""
        family = self.sim.world.gameobjects.get_gameobject(family_id)

        family_component = family.get_component(Family)

        output: list[str] = [
            f"# [Family] {family.name_with_uid}\n",
            "\n",
            f"Name: {family_component.name}\n",
        ]

        parent_family = (
            family_component.parent_family.name_with_uid
            if family_component.parent_family
            else "None"
        )

        output.append(f"Parent Family: {parent_family}\n")

        if len(family_component.branch_families) > 0:
            output.append("Branch Families:\n")
            for branch_family in family_component.branch_families:
                output.append(f"- {branch_family.name_with_uid}")
        else:
            output.append("Branch Families: None\n")

        head_name = (
            family_component.head.name_with_uid if family_component.head else "None"
        )
        output.append(f"Current Head: {head_name}\n")

        if len(family_component.former_heads) > 0:
            output.append("Former Heads:\n")
            for former_head in family_component.former_heads:
                output.append(f"- {former_head.name_with_uid}\n")
        else:
            output.append("Former Heads: None\n")

        if len(family_component.active_members) > 0:
            active_members = ", ".join(
                m.name_with_uid for m in family_component.active_members
            )
            output.append(f"Active Members: {active_members}\n")
        else:
            output.append("Active Members: None")

        if len(family_component.former_members) > 0:
            former_members = ", ".join(
                m.name_with_uid for m in family_component.former_members
            )
            output.append(f"Former Members: {former_members}\n")
        else:
            output.append("Former Members: None\n")

        if family_component.alliance is not None:
            alliance_component = family_component.alliance.get_component(Alliance)
            output.append("Alliance:")
            for alliance_member in alliance_component.member_families:
                if alliance_member != family:
                    output.append(f"- {alliance_member.name_with_uid}\n")
        else:
            output.append("Alliance: None\n")

        home_base = (
            family_component.home_base.name_with_uid
            if family_component.home_base
            else "None"
        )
        output.append(f"Home Base: {home_base}\n")

        if len(family_component.territories) > 0:
            territories = ", ".join(
                t.name_with_uid for t in family_component.territories
            )
            output.append(f"Territories: {territories}\n")
        else:
            output.append("Territories: None\n")

        if len(family_component.warriors) > 0:
            warriors = ", ".join(w.name_with_uid for w in family_component.warriors)
            output.append(f"Warriors: {warriors}\n")
        else:
            output.append("Warriors: None\n")

        if len(family_component.advisors) > 0:
            advisors = ", ".join(a.name_with_uid for a in family_component.advisors)
            output.append(f"Advisors: {advisors}\n")
        else:
            output.append("Advisors: None\n")

        console = rich.console.Console()
        markdown_obj = rich.markdown.Markdown("\n".join(output))
        console.print(markdown_obj)

    def inspect_territory(self, territory_id: int) -> None:
        """Print information about a territory."""
        territory = self.sim.world.gameobjects.get_gameobject(territory_id)

        territory_component = territory.get_component(Territory)

        output = [
            f"# [Territory] {territory.name_with_uid}",
            "",
            f"Name: {territory.name!r}\n",
        ]

        # Add controlling family information
        if territory_component.controlling_family:
            output.append(
                f"Controlling Family: {territory_component.controlling_family.name_with_uid}\n"
            )
        else:
            output.append("Controlling Family: None\n")

        # Add neighbors
        output.append("Neighboring Territories:\n")
        for neighbor in territory_component.neighbors:
            output.append(f"- {neighbor.name_with_uid}\n")

        # Add families
        output.append("Resident Families:\n")
        for family in territory_component.families:
            output.append(f"- {family.name_with_uid}\n")

        table = rich.table.Table(
            "Family", "Influence", title="Political Influences", title_justify="left"
        )
        for family, influence in territory_component.political_influence.items():
            table.add_row(f"{family.name_with_uid}", f"{influence}")

        console = rich.console.Console()
        markdown_obj = rich.markdown.Markdown("\n".join(output))
        console.print(markdown_obj)
        console.print("===\n")
        console.print(table)

    def inspect_dynasty(self, dynasty_id: int) -> None:
        """Print information about a dynasty."""
        dynasty = self.sim.world.gameobjects.get_gameobject(dynasty_id)

        dynasty_component = dynasty.get_component(Dynasty)

        output: list[str] = [
            f"# [Dynasty] {dynasty.name_with_uid}\n",
            "",
        ]

        current_ruler = (
            dynasty_component.current_ruler.name_with_uid
            if dynasty_component.current_ruler
            else "None"
        )

        if len(dynasty_component.previous_rulers) > 0:
            previous_rulers = ", ".join(
                r.name_with_uid for r in dynasty_component.previous_rulers
            )
        else:
            previous_rulers = "None"

        previous_dynasty = (
            dynasty_component.previous_dynasty.name_with_uid
            if dynasty_component.previous_dynasty
            else "None"
        )

        output.append(f"Current Ruler: {current_ruler}\n")
        output.append(f"Founder: {dynasty_component.founder.name_with_uid}\n")
        output.append(f"Family: {dynasty_component.family.name_with_uid}\n")
        output.append(f"Founding Date: {dynasty_component.founding_date}\n")
        output.append(f"Ending Date: {dynasty_component.ending_date}\n")
        output.append(f"Previous Rulers: {previous_rulers}\n")
        output.append(f"Previous Dynasty: {previous_dynasty}\n")

        console = rich.console.Console()
        markdown_obj = rich.markdown.Markdown("\n".join(output))
        console.print(markdown_obj)

    def list_dynasties(self) -> None:
        """Print information about the current dynasty."""
        dynasty_tracker = self.sim.world.resources.get_resource(DynastyTracker)

        table = rich.table.Table(show_header=True, title="Dynasties")
        table.add_column("Is Current", justify="right")
        table.add_column("UID")
        table.add_column("Family")
        table.add_column("Start Date")
        table.add_column("End Date")

        results = sorted(self.sim.world.get_components((Dynasty,)), key=lambda e: e[0])

        for uid, (dynasty,) in results:

            family_name: str = dynasty.family.name_with_uid

            is_current_marker = (
                "⭐️" if dynasty.gameobject == dynasty_tracker.current_dynasty else ""
            )

            table.add_row(
                f"{is_current_marker}",
                f"{uid}",
                f"{family_name}",
                f"{dynasty.founding_date}",
                f"{dynasty.ending_date}",
            )

        console = rich.console.Console()
        console.print(table)

    def list_territories(self) -> None:
        """Print the list of territories in the simulation."""

        table = rich.table.Table(show_header=True, title="Territories")
        table.add_column("Name")
        table.add_column("Controlling Family")

        for _, (territory,) in self.sim.world.get_components((Territory,)):

            controlling_family_name: str = (
                territory.controlling_family.name_with_uid
                if territory.controlling_family
                else "None"
            )

            table.add_row(
                f"{territory.gameobject.name_with_uid}",
                f"{controlling_family_name}",
            )

        console = rich.console.Console()
        console.print(table)

    def list_characters(self, inactive_ok: bool = False) -> None:
        """Print a list of characters from the simulation."""
        table = rich.table.Table(show_header=True, title="Characters")

        table.add_column("Name")
        table.add_column("Age")
        table.add_column("Sex")
        table.add_column("Family")

        for _, (character,) in self.sim.world.get_components((Character,)):
            if not inactive_ok and not character.gameobject.has_component(Active):
                continue

            family_name: str = (
                character.family.name_with_uid if character.family else "None"
            )

            table.add_row(
                f"{character.gameobject.name_with_uid}",
                f"{int(character.age)}",
                f"{character.sex.name}",
                f"{family_name}",
            )

        console = rich.console.Console()
        console.print(table)

    def list_families(self, inactive_ok: bool = False) -> None:
        """Print all the families in the simulation."""
        table = rich.table.Table(show_header=True, title="Families")
        table.add_column("Name")
        table.add_column("Family Head")
        table.add_column("Home Base")

        for _, (family,) in self.sim.world.get_components((Family,)):
            if not inactive_ok and not family.gameobject.has_component(Active):
                continue

            family_head: str = family.head.name_with_uid if family.head else "None"

            home_base: str = (
                family.home_base.name_with_uid if family.home_base else "None"
            )

            table.add_row(
                f"{family.gameobject.name_with_uid}", f"{family_head}", f"{home_base}"
            )

        console = rich.console.Console()
        console.print(table)

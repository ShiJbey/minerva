"""Simulation inspection helper functions.

Tools and helper functions for inspecting simulations.

"""

from typing import Any

import rich.columns
import rich.console
import rich.markdown
import rich.panel
import rich.table

from minerva import __version__
from minerva.actions.base_types import Scheme, SchemeManager
from minerva.characters.components import (
    Betrothal,
    Boldness,
    Character,
    Compassion,
    Diplomacy,
    Dynasty,
    DynastyTracker,
    Ruler,
    Family,
    FamilyRoleFlags,
    Fertility,
    Greed,
    HeadOfFamily,
    Honor,
    Intelligence,
    Intrigue,
    Lifespan,
    Luck,
    Marriage,
    Martial,
    Pregnancy,
    Prowess,
    Rationality,
    RomancePropensity,
    RomanticAffair,
    Sociability,
    Stewardship,
    Vengefulness,
)
from minerva.characters.metric_data import CharacterMetrics
from minerva.characters.succession_helpers import get_current_ruler
from minerva.characters.war_data import Alliance, War
from minerva.ecs import Active
from minerva.life_events.base_types import LifeEventHistory
from minerva.simulation import Simulation
from minerva.stats.base_types import StatusEffectManager
from minerva.traits.base_types import TraitManager
from minerva.world_map.components import PopulationHappiness, Territory


class SimulationInspector:
    """A helper class for printing various simulation info to the terminal."""

    __slots__ = ("sim",)

    sim: Simulation

    def __init__(self, sim: Simulation) -> None:
        self.sim = sim

    def print_status(self) -> None:
        """Print the current status of the simulation."""

        total_characters = len(
            list(self.sim.world.query_components((Character, Active)))
        )
        total_families = len(list(self.sim.world.query_components((Family, Active))))
        total_territories = len(
            list(self.sim.world.query_components((Territory, Active)))
        )
        total_wars = len(list(self.sim.world.query_components((War, Active))))
        total_alliances = len(list(self.sim.world.query_components((Alliance, Active))))
        current_ruler = get_current_ruler(self.sim.world)
        current_ruler_name = current_ruler.name_with_uid if current_ruler else "None"

        console = rich.console.Console()

        panel = rich.panel.Panel(
            f"[orange1 bold]World seed:[/orange1 bold] {self.sim.config.seed}\n"
            f"[orange1 bold]World Date:[/orange1 bold] {self.sim.date.to_iso_str()}\n"
            f"[orange1 bold]Simulation Version:[/orange1 bold] {__version__}\n"
            f"[orange1 bold]Num Active Families:[/orange1 bold] {total_families}\n"
            f"[orange1 bold]Num Active Characters:[/orange1 bold] {total_characters}\n"
            f"[orange1 bold]Current Ruler:[/orange1 bold] {current_ruler_name}\n"
            f"[orange1 bold]Num Active Territories:[/orange1 bold] {total_territories}\n"
            f"[orange1 bold]Num Active Wars:[/orange1 bold] {total_wars}\n"
            f"[orange1 bold]Num Active Alliances:[/orange1 bold] {total_alliances}",
            title="Simulation Info",
            title_align="left",
            expand=False,
            highlight=True,
        )

        console.print(panel)

    def inspect(self, entity_id: int) -> None:
        """Print information about an entity."""

        if self.sim.world.entity_exists(entity_id):
            entity = self.sim.world.get_entity(entity_id)

            if entity.has_component(Character):
                self.inspect_character(entity_id)
            elif entity.has_component(Family):
                self.inspect_family(entity_id)
            elif entity.has_component(Territory):
                self.inspect_territory(entity_id)
            elif entity.has_component(Dynasty):
                self.inspect_dynasty(entity_id)
            elif entity.has_component(War):
                self.inspect_war(entity_id)
            elif entity.has_component(Alliance):
                self.inspect_alliance(entity_id)
            else:
                console = rich.console.Console()
                console.print(rich.markdown.Markdown(f"# {entity.name_with_uid}"))
                rich.inspect(entity)

        else:
            console = rich.console.Console()
            console.print(
                "[red bold]Error:[/red bold] No entity found with id: " f"{entity_id}."
            )

    def inspect_war(self, war_id: int) -> None:
        """Print information about a war."""
        console = rich.console.Console()

        war = self.sim.world.get_entity(war_id)

        war_component = war.get_component(War)

        aggressor = war_component.aggressor.name_with_uid
        defender = war_component.defender.name_with_uid
        aggressor_allies = ", ".join(
            a.name_with_uid for a in war_component.aggressor_allies
        )
        defender_allies = ", ".join(
            a.name_with_uid for a in war_component.defender_allies
        )
        contested_territory = war_component.contested_territory.name_with_uid
        start_date = str(war_component.start_date)
        end_date = str(war_component.end_date)

        console.print(
            rich.panel.Panel(
                f"[orange1 bold]Aggressor[/orange1 bold]: {aggressor}\n"
                f"[orange1 bold]Defender[/orange1 bold]: {defender}\n"
                f"[orange1 bold]Aggressor Allies[/orange1 bold]: {aggressor_allies}\n"
                f"[orange1 bold]Defender Allies[/orange1 bold]: {defender_allies}\n"
                f"[orange1 bold]Contested Territory[/orange1 bold]: {contested_territory}\n"
                f"[orange1 bold]Start Date[/orange1 bold]: {start_date}\n"
                f"[orange1 bold]End Date[/orange1 bold]: {end_date}",
                title=f"War ({war_id})",
                title_align="left",
                expand=False,
                highlight=True,
            )
        )

    def inspect_alliance(self, alliance_id: int) -> None:
        """Print information about an alliance to the console."""
        alliance = self.sim.world.get_entity(alliance_id)
        alliance_component = alliance.get_component(Alliance)

        founder = alliance_component.founder.name_with_uid
        founder_family = alliance_component.founder_family.name_with_uid
        members = ", ".join(m.name_with_uid for m in alliance_component.member_families)
        start_date = str(alliance_component.start_date)
        end_date = str(alliance_component.end_date)

        console = rich.console.Console()
        console.print(
            rich.panel.Panel(
                f"[orange1 bold]Founder[/orange1 bold]: {founder}\n"
                f"[orange1 bold]Founder Family[/orange1 bold]: {founder_family}\n"
                f"[orange1 bold]Members[/orange1 bold]: {members}\n"
                f"[orange1 bold]Start Date[/orange1 bold]: {start_date}\n"
                f"[orange1 bold]End Date[/orange1 bold]: {end_date}",
                title=f"Alliance ({alliance_id})",
                title_align="left",
                expand=False,
                highlight=True,
            )
        )

    def inspect_character(self, character_id: int) -> None:
        """Print information about a character to the console."""

        renderable_objs: list[Any] = []

        character = self.sim.world.get_entity(character_id)

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
        former_spouses = (
            ", ".join(
                x.get_component(Marriage).spouse.name_with_uid
                for x in character_component.past_marriages
            )
            if character_component.past_marriages
            else None
        )
        betrothed_to = (
            character_component.betrothed_to.name_with_uid
            if character_component.betrothed_to
            else "None"
        )
        former_betrothals = (
            ", ".join(
                x.get_component(Betrothal).betrothed.name_with_uid
                for x in character_component.past_betrothals
            )
            if character_component.past_betrothals
            else None
        )
        lover = (
            character_component.lover.name_with_uid
            if character_component.lover
            else "None"
        )
        former_lovers = (
            ", ".join(
                x.get_component(RomanticAffair).lover.name_with_uid
                for x in character_component.past_love_affairs
            )
            if character_component.past_love_affairs
            else None
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
        siblings = (
            ", ".join(s.name_with_uid for s in character_component.siblings)
            if character_component.siblings
            else None
        )
        children = (
            ", ".join(s.name_with_uid for s in character_component.children)
            if character_component.children
            else None
        )
        family_roles = ", ".join(
            str(r.name)
            for r in FamilyRoleFlags
            if r in character_component.family_roles
        )

        title_list: list[str] = []

        if character.has_component(Ruler):
            title_list.append("Ruler")

        if character.has_component(HeadOfFamily):
            head_of_family_comp = character.get_component(HeadOfFamily)
            title_list.append(
                f"Head of {head_of_family_comp.family.name_with_uid} family"
            )

        titles = ", ".join(title_list) if title_list else "N/A"

        trait_manager = character.get_component(TraitManager)
        traits = ", ".join(entry.name for entry in trait_manager.traits.values())

        demographic_info = (
            "[orange1 bold]First Name[/orange1 bold]:"
            f"{character_component.first_name}\n"
            f"[orange1 bold]Surname[/orange1 bold]: {character_component.surname}\n"
            "[orange1 bold]Surname at Birth[/orange1 bold]: "
            f"{character_component.birth_surname}\n"
            "[orange1 bold]Age[/orange1 bold]: "
            f"{int(character_component.age)} ({character_component.life_stage.name})\n"
            "[orange1 bold]Sex[/orange1 bold]: "
            f"{character_component.sex.name.lower()}\n"
            "[orange1 bold]Sexual Orientation[/orange1 bold]: "
            f"{character_component.sexual_orientation.name.lower()}\n"
            f"[orange1 bold]Is Alive[/orange1 bold]: {character_component.is_alive}\n"
            f"[orange1 bold]Titles[/orange1 bold]: {titles}\n"
            "[orange1 bold]Birth Date[/orange1 bold]: "
            f"{character_component.birth_date}\n"
            "[orange1 bold]Death Date[/orange1 bold]: "
            f"{character_component.death_date}\n"
            f"[orange1 bold]Traits[/orange1 bold]: {traits}\n"
            f"[orange1 bold]Family[/orange1 bold]: {family}\n"
            f"[orange1 bold]Family Roles[/orange1 bold]: {family_roles}\n"
            f"[orange1 bold]Birth Family[/orange1 bold]: {birth_family}"
        )

        general_info_panel = rich.panel.Panel(
            demographic_info,
            title="Demographic Info",
            title_align="left",
            expand=False,
            highlight=True,
        )

        renderable_objs.append(general_info_panel)

        if character.has_component(Pregnancy):
            pregnancy = character.get_component(Pregnancy)
            conception = str(pregnancy.conception_date)
            due = str(pregnancy.due_date)
            assumed_father = (
                pregnancy.assumed_father.name_with_uid
                if pregnancy.assumed_father
                else "None"
            )
            actual_father = pregnancy.actual_father.name_with_uid

            pregnancy_panel = rich.panel.Panel(
                f"[bold]This character is pregnant[/bold]\n"
                f"[orange1 bold]Conception Date[/orange1 bold]: {conception}\n"
                f"[orange1 bold]Due Date[/orange1 bold]: {due}\n"
                f"[orange1 bold]Assumed Father[/orange1 bold]: {assumed_father}\n"
                f"[orange1 bold]Actual Father[/orange1 bold]: {actual_father}",
                title="Pregnancy",
                title_align="left",
                expand=False,
                highlight=True,
            )
            renderable_objs.append(pregnancy_panel)

        if character.has_component(Ruler):
            dynasty_tracker = self.sim.world.get_resource(DynastyTracker)
            current_dynasty = dynasty_tracker.current_dynasty
            assert current_dynasty
            ruler_panel = rich.panel.Panel(
                f"[bold]This character is the current ruler[/bold]\n"
                f"[orange1 bold]Dynasty[/orange1 bold]: {current_dynasty.name_with_uid}",
                title="Ruler",
                title_align="left",
                expand=False,
                highlight=True,
            )
            renderable_objs.append(ruler_panel)

        metrics = character.get_component(CharacterMetrics).data
        metrics_str = (
            f"[orange1 bold]Times Married[/orange1 bold]: {metrics.times_married}\n"
            f"[orange1 bold]# Wars[/orange1 bold]: {metrics.num_wars}\n"
            f"[orange1 bold]# Wars Started[/orange1 bold]: {metrics.num_wars_started}\n"
            f"[orange1 bold]# Wars Won[/orange1 bold]: {metrics.num_wars_won}\n"
            f"[orange1 bold]# Wars Lost[/orange1 bold]: {metrics.num_wars_lost}\n"
            f"[orange1 bold]# Revolts Quelled[/orange1 bold]: {metrics.num_revolts_quelled}\n"
            f"[orange1 bold]# Coups Planned[/orange1 bold]: {metrics.num_coups_planned}\n"
            f"[orange1 bold]# Territories Taken[/orange1 bold]: {metrics.num_territories_taken}\n"
            f"[orange1 bold]Times as Ruler[/orange1 bold]: {metrics.times_as_ruler}\n"
            f"[orange1 bold]# Alliances Founded[/orange1 bold]: {metrics.num_alliances_founded}\n"
            f"[orange1 bold]# Failed Alliance Schemes[/orange1 bold]: {metrics.num_failed_alliance_attempts}\n"
            f"[orange1 bold]# Alliances Disbanded[/orange1 bold]: {metrics.num_alliances_disbanded}\n"
            f"[orange1 bold]Inherited Throne?[/orange1 bold]: {metrics.directly_inherited_throne}\n"
            f"[orange1 bold]Last Declared War[/orange1 bold]: {metrics.date_of_last_declared_war}"
        )

        metrics_panel = rich.panel.Panel(
            metrics_str,
            title="Character Metrics",
            title_align="left",
            expand=False,
            highlight=True,
        )
        renderable_objs.append(metrics_panel)

        relations_panel = rich.panel.Panel(
            f"[orange1 bold]Mother[/orange1 bold]: {mother}\n"
            f"[orange1 bold]Father[/orange1 bold]: {father}\n"
            f"[orange1 bold]Biological Father[/orange1 bold]: {biological_father}\n"
            f"[orange1 bold]Siblings[/orange1 bold]: {siblings}\n"
            f"[orange1 bold]Children[/orange1 bold]: {children}\n"
            f"[orange1 bold]Spouse[/orange1 bold]: {spouse}\n"
            f"[orange1 bold]Former Spouses[/orange1 bold]: {former_spouses}\n"
            f"[orange1 bold]Betrothed To[/orange1 bold]: {betrothed_to}\n"
            f"[orange1 bold]Former Betrothals[/orange1 bold]: {former_betrothals}\n"
            f"[orange1 bold]Lover[/orange1 bold]: {lover}\n"
            f"[orange1 bold]Former Lovers[/orange1 bold]: {former_lovers}\n"
            f"[orange1 bold]Heir[/orange1 bold]: {heir}\n"
            f"[orange1 bold]Heir To[/orange1 bold]: {heir_to}",
            title="Relations",
            title_align="left",
            expand=False,
            highlight=True,
        )
        renderable_objs.append(relations_panel)

        status_effect_manager = character.get_component(StatusEffectManager)
        effect_names = ", ".join(e.name for e in status_effect_manager.status_effects)
        status_effects_panel = rich.panel.Panel(
            f"[orange1 bold]Active Effects[/orange1 bold]: {effect_names}",
            title="Status Effects",
            title_align="left",
            expand=False,
            highlight=True,
        )
        renderable_objs.append(status_effects_panel)

        stat_columns: list[str] = []
        stat_columns.append(
            "[orange1 bold]Influence Points[/orange1 bold]: "
            f"{int(character_component.influence_points)}"
        )
        lifespan = character.get_component(Lifespan).value
        stat_columns.append("[orange1 bold]Lifespan[/orange1 bold]: " f"{lifespan:.2f}")
        fertility = character.get_component(Fertility).value
        stat_columns.append(
            "[orange1 bold]Fertility[/orange1 bold]: " f"{fertility:.2f}"
        )
        stewardship = character.get_component(Stewardship).value
        stat_columns.append(
            "[orange1 bold]Stewardship[/orange1 bold]: " f"{stewardship:.2f}"
        )
        martial = character.get_component(Martial).value
        stat_columns.append("[orange1 bold]Martial[/orange1 bold]: " f"{martial:.2f}")
        intrigue = character.get_component(Intrigue).value
        stat_columns.append("[orange1 bold]Intrigue[/orange1 bold]: " f"{intrigue:.2f}")
        intelligence = character.get_component(Intelligence).value
        stat_columns.append(
            "[orange1 bold]intelligence[/orange1 bold]: " f"{intelligence:.2f}"
        )
        prowess = character.get_component(Prowess).value
        stat_columns.append("[orange1 bold]Prowess[/orange1 bold]: " f"{prowess:.2f}")
        sociability = character.get_component(Sociability).value
        stat_columns.append(
            "[orange1 bold]Sociability[/orange1 bold]: " f"{sociability:.2f}"
        )
        honor = character.get_component(Honor).value
        stat_columns.append("[orange1 bold]Honor[/orange1 bold]: " f"{honor:.2f}")
        boldness = character.get_component(Boldness).value
        stat_columns.append("[orange1 bold]Boldness[/orange1 bold]: " f"{boldness:.2f}")
        compassion = character.get_component(Compassion).value
        stat_columns.append(
            "[orange1 bold]Compassion[/orange1 bold]: " f"{compassion:.2f}"
        )
        diplomacy = character.get_component(Diplomacy).value
        stat_columns.append(
            "[orange1 bold]Diplomacy[/orange1 bold]: " f"{diplomacy:.2f}"
        )
        greed = character.get_component(Greed).value
        stat_columns.append("[orange1 bold]Greed[/orange1 bold]: " f"{greed:.2f}")
        rationality = character.get_component(Rationality).value
        stat_columns.append(
            "[orange1 bold]Rationality[/orange1 bold]: " f"{rationality:.2f}"
        )
        vengefulness = character.get_component(Vengefulness).value
        stat_columns.append(
            "[orange1 bold]Vengefulness[/orange1 bold]: " f"{vengefulness:.2f}"
        )
        romance_propensity = character.get_component(RomancePropensity).value
        stat_columns.append(
            "[orange1 bold]Romance Propensity[/orange1 bold]: "
            f"{romance_propensity:.2f}"
        )
        luck = character.get_component(Luck).value
        stat_columns.append("[orange1 bold]Luck[/orange1 bold]: " f"{luck:.2f}")

        stats_panel = rich.panel.Panel(
            rich.columns.Columns(stat_columns, expand=False, equal=True),
            title="Stats",
            title_align="left",
            expand=False,
        )
        renderable_objs.append(stats_panel)

        scheme_table = rich.table.Table(
            "UID", "SchemeType", "Initiator", "members", highlight=True
        )
        scheme_manager = character.get_component(SchemeManager)
        for scheme in scheme_manager.schemes:
            scheme_component = scheme.get_component(Scheme)
            scheme_table.add_row(
                str(scheme.uid),
                str(scheme_component.get_type()),
                str(scheme_component.initiator.name_with_uid),
                ", ".join(m.name_with_uid for m in scheme_component.members),
            )

        scheme_panel = rich.panel.Panel(
            scheme_table,
            title="Schemes",
            title_align="left",
            expand=False,
        )
        renderable_objs.append(scheme_panel)

        life_event_history = character.get_component(LifeEventHistory)

        life_event_table = rich.table.Table("Timestamp", "Description", highlight=True)
        for event in life_event_history.get_history():
            life_event_table.add_row(str(event.timestamp), event.get_description())

        life_event_panel = rich.panel.Panel(
            life_event_table,
            title="Life Events",
            title_align="left",
            expand=False,
        )

        renderable_objs.append(life_event_panel)

        console = rich.console.Console()
        console.print(
            rich.panel.Panel(
                rich.console.Group(*renderable_objs),
                title=character.name_with_uid,
                title_align="left",
                expand=False,
                highlight=True,
                padding=(1, 1),
            )
        )

    def inspect_family(self, family_id: int) -> None:
        """Print information about a family."""
        family = self.sim.world.get_entity(family_id)

        family_component = family.get_component(Family)

        parent_family = (
            family_component.parent_family.name_with_uid
            if family_component.parent_family
            else "None"
        )

        branch_families = (
            ", ".join(b.name_with_uid for b in family_component.branch_families)
            if family_component.branch_families
            else "None"
        )

        head_name = (
            family_component.head.name_with_uid if family_component.head else "None"
        )

        former_heads = (
            ", ".join(f.name_with_uid for f in family_component.former_heads)
            if family_component.former_heads
            else "None"
        )

        active_members = (
            ", ".join(m.name_with_uid for m in family_component.active_members)
            if family_component.active_members
            else "None"
        )

        former_members = (
            ", ".join(m.name_with_uid for m in family_component.former_members)
            if family_component.former_members
            else "None"
        )

        allies: str = "None"
        if family_component.alliance is not None:
            alliance_component = family_component.alliance.get_component(Alliance)
            allies_list: list[str] = []
            for alliance_member in alliance_component.member_families:
                if alliance_member != family:
                    allies_list.append(alliance_member.name_with_uid)
            allies = ", ".join(allies_list)

        home_base = (
            family_component.home_base.name_with_uid
            if family_component.home_base
            else "None"
        )

        territories = (
            ", ".join(t.name_with_uid for t in family_component.territories_present_in)
            if family_component.territories_present_in
            else "None"
        )

        controlled_territories = (
            ", ".join(t.name_with_uid for t in family_component.controlled_territories)
            if family_component.controlled_territories
            else "None"
        )

        warriors = (
            ", ".join(w.name_with_uid for w in family_component.warriors)
            if family_component.warriors
            else "None"
        )
        advisors = (
            ", ".join(a.name_with_uid for a in family_component.advisors)
            if family_component.advisors
            else "None"
        )

        general_info_panel = rich.panel.Panel(
            f"[orange1 bold]Name[/orange1 bold]: {family.name}\n"
            f"[orange1 bold]Is Active[/orange1 bold]: {family.is_active}\n"
            f"[orange1 bold]Parent Family[/orange1 bold]: {parent_family}\n"
            f"[orange1 bold]Branch Families[/orange1 bold]: {branch_families}\n"
            f"[orange1 bold]Family Head[/orange1 bold]: {head_name}\n"
            f"[orange1 bold]Active Members[/orange1 bold]: {active_members}\n"
            f"[orange1 bold]Former Heads[/orange1 bold]: {former_heads}\n"
            f"[orange1 bold]Former Members[/orange1 bold]: {former_members}\n"
            f"[orange1 bold]Home Base[/orange1 bold]: {home_base}\n"
            f"[orange1 bold]Territories[/orange1 bold]: {territories}\n"
            f"[orange1 bold]Controlled Territories[/orange1 bold]: {controlled_territories}\n"
            f"[orange1 bold]Warriors[/orange1 bold]: {warriors}\n"
            f"[orange1 bold]Advisors[/orange1 bold]: {advisors}\n"
            f"[orange1 bold]Allied Families[/orange1 bold]: {allies}",
            title="Family Info",
            title_align="left",
            highlight=True,
            expand=False,
        )

        console = rich.console.Console()
        console.print(
            rich.panel.Panel(
                rich.console.Group(
                    general_info_panel,
                ),
                title=f"The {family.name} Family ({family.uid})",
                title_align="left",
                expand=False,
                highlight=True,
                padding=(1, 1),
            )
        )

    def inspect_territory(self, territory_id: int) -> None:
        """Print information about a territory."""
        territory = self.sim.world.get_entity(territory_id)

        territory_component = territory.get_component(Territory)

        name = territory_component.name

        # Add controlling family information
        controlling_family = (
            territory_component.controlling_family.name_with_uid
            if territory_component.controlling_family
            else "None"
        )

        # Add neighbors
        neighbors = ", ".join(n.name_with_uid for n in territory_component.neighbors)

        # Add families
        resident_families = ", ".join(
            f.name_with_uid for f in territory_component.families
        )

        political_influence_table = rich.table.Table(
            "Family", "Influence", title_justify="left", highlight=True
        )
        for family, influence in territory_component.political_influence.items():
            political_influence_table.add_row(f"{family.name_with_uid}", f"{influence}")

        console = rich.console.Console()

        happiness = territory.get_component(PopulationHappiness).value

        general_info_panel = rich.panel.Panel(
            f"[orange1 bold]Name[/orange1 bold]: {name}\n"
            f"[orange1 bold]Controlling Family[/orange1 bold]: {controlling_family}\n"
            f"[orange1 bold]Neighboring Territories[/orange1 bold]: {neighbors}\n"
            f"[orange1 bold]Resident Families[/orange1 bold]: {resident_families}",
            title="Territory Info",
            title_align="left",
            expand=False,
            highlight=True,
        )

        stats_panel = rich.panel.Panel(
            "[orange1 bold]Population Happiness[/orange1 bold]: " f"{happiness:.2f}",
            title="Stats",
            title_align="left",
            expand=False,
            highlight=True,
        )

        political_influence_panel = rich.panel.Panel(
            political_influence_table,
            title="Political Influence",
            title_align="left",
            expand=False,
            highlight=True,
        )

        console.print(
            rich.panel.Panel(
                rich.console.Group(
                    general_info_panel,
                    stats_panel,
                    political_influence_panel,
                ),
                title=territory.name_with_uid,
                title_align="left",
                expand=False,
                highlight=True,
                padding=(1, 1),
            )
        )

    def inspect_dynasty(self, dynasty_id: int) -> None:
        """Print information about a dynasty."""
        dynasty = self.sim.world.get_entity(dynasty_id)

        dynasty_component = dynasty.get_component(Dynasty)

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

        console = rich.console.Console()

        general_info_panel = rich.panel.Panel(
            f"[orange1 bold]Current Ruler[/orange1 bold]: {current_ruler}\n"
            f"[orange1 bold]Founder[/orange1 bold]: {dynasty_component.founder.name_with_uid}\n"
            f"[orange1 bold]Family[/orange1 bold]: {dynasty_component.family.name_with_uid}\n"
            f"[orange1 bold]Founding Date[/orange1 bold]: {dynasty_component.founding_date}\n"
            f"[orange1 bold]Ending Date[/orange1 bold]: {dynasty_component.ending_date}\n"
            f"[orange1 bold]Previous Rulers[/orange1 bold]: {previous_rulers}\n"
            f"[orange1 bold]Previous Dynasty[/orange1 bold]: {previous_dynasty}",
        )

        console.print(
            rich.panel.Panel(
                rich.console.Group(
                    general_info_panel,
                ),
                title=dynasty.name_with_uid,
                title_align="left",
                expand=False,
                highlight=True,
                padding=(1, 1),
            )
        )

    def list_dynasties(self) -> None:
        """Print information about the current dynasty."""
        dynasty_tracker = self.sim.world.get_resource(DynastyTracker)

        table = rich.table.Table(show_header=True, title="Dynasties", highlight=True)
        table.add_column("Current Dynasty", justify="right")
        table.add_column("UID")
        table.add_column("Family")
        table.add_column("Start Date")
        table.add_column("End Date")

        results = sorted(
            self.sim.world.query_components((Dynasty,)), key=lambda e: e[0]
        )

        for uid, (dynasty,) in results:

            family_name: str = dynasty.family.name_with_uid

            is_current_marker = (
                "==>" if dynasty.entity == dynasty_tracker.current_dynasty else ""
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

        table = rich.table.Table(show_header=True, title="Territories", highlight=True)
        table.add_column("Name")
        table.add_column("Controlling Family")

        for _, (territory,) in self.sim.world.query_components((Territory,)):

            controlling_family_name: str = (
                territory.controlling_family.name_with_uid
                if territory.controlling_family
                else "None"
            )

            table.add_row(
                f"{territory.entity.name_with_uid}",
                f"{controlling_family_name}",
            )

        console = rich.console.Console()
        console.print(table)

    def list_characters(self, inactive_ok: bool = False) -> None:
        """Print a list of characters from the simulation."""
        table = rich.table.Table(show_header=True, title="Characters", highlight=True)

        table.add_column("Name")
        table.add_column("Age")
        table.add_column("Sex")
        table.add_column("Family")

        for _, (character,) in self.sim.world.query_components((Character,)):
            if not inactive_ok and not character.entity.has_component(Active):
                continue

            family_name: str = (
                character.family.name_with_uid if character.family else "None"
            )

            table.add_row(
                f"{character.entity.name_with_uid}",
                f"{int(character.age)}",
                f"{character.sex.name}",
                f"{family_name}",
            )

        console = rich.console.Console()
        console.print(table)

    def list_families(self, inactive_ok: bool = False) -> None:
        """Print all the families in the simulation."""
        table = rich.table.Table(show_header=True, title="Families", highlight=True)
        table.add_column("Name")
        table.add_column("Family Head")
        table.add_column("Home Base")

        for _, (family,) in self.sim.world.query_components((Family,)):
            if not inactive_ok and not family.entity.has_component(Active):
                continue

            family_head: str = family.head.name_with_uid if family.head else "None"

            home_base: str = (
                family.home_base.name_with_uid if family.home_base else "None"
            )

            table.add_row(
                f"{family.entity.name_with_uid}", f"{family_head}", f"{home_base}"
            )

        console = rich.console.Console()
        console.print(table)

    def list_alliances(self, inactive_ok: bool = False) -> None:
        """Print all active alliances."""

        if inactive_ok:
            alliances = [
                (uid, f) for uid, (f,) in self.sim.world.query_components((Alliance,))
            ]
        else:
            alliances = [
                (uid, f)
                for uid, (f, _) in self.sim.world.query_components((Alliance, Active))
            ]

        table = rich.table.Table(show_header=True, title="Alliances", highlight=True)
        table.add_column("UID")
        table.add_column("Start Date")
        table.add_column("Founder")
        table.add_column("Members")

        for uid, alliance in alliances:
            table.add_row(
                str(uid),
                str(alliance.start_date),
                str(alliance.founder.name_with_uid),
                ", ".join(m.name_with_uid for m in alliance.member_families),
            )

        console = rich.console.Console()
        console.print(table)

    def list_wars(self, inactive_ok: bool = False) -> None:
        """Print all active wars."""

        if inactive_ok:
            wars = [(uid, f) for uid, (f,) in self.sim.world.query_components((War,))]
        else:
            wars = [
                (uid, f)
                for uid, (f, _) in self.sim.world.query_components((War, Active))
            ]

        table = rich.table.Table(show_header=True, title="Wars", highlight=True)
        table.add_column("UID")
        table.add_column("Start Date")
        table.add_column("Aggressor")
        table.add_column("Defender")
        table.add_column("Territory")

        for uid, war in wars:
            table.add_row(
                str(uid),
                str(war.start_date),
                str(war.aggressor.name_with_uid),
                str(war.defender.name_with_uid),
                str(war.contested_territory.name_with_uid),
            )

        console = rich.console.Console()
        console.print(table)

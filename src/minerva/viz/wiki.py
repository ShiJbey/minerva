"""PyGame Minerva World Wiki Explorer."""

import pathlib
from abc import ABC, abstractmethod
from typing import Any
from urllib.parse import parse_qs, urlparse

import pygame
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pygame_gui import (
    UI_BUTTON_PRESSED,
    UI_TEXT_BOX_LINK_CLICKED,
    UI_TEXT_ENTRY_FINISHED,
)
from pygame_gui.elements import UIButton, UILabel, UITextBox, UITextEntryLine, UIWindow
from pygame_gui.ui_manager import UIManager

from minerva.characters.components import Character, Clan, Family
from minerva.ecs import Active, GameObject
from minerva.settlements.base_types import Settlement, PopulationHappiness
from minerva.simulation import Simulation


class WikiPageGenerator(ABC):
    """Generates pygame-gui-compatible HTML pages for the world wiki window."""

    @abstractmethod
    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        """Generate a new page."""
        raise NotImplementedError


_jinja_env = Environment(
    loader=FileSystemLoader(pathlib.Path(__file__).parent / "resources" / "templates"),
    autoescape=select_autoescape(),
)


class IndexPageGenerator(WikiPageGenerator):
    """Generates the index page for the wiki window."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("index.jinja")
        content = template.render(world_seed=sim.config.seed)
        content = content.replace("\n", "")
        return content


class SettlementListPageGenerator(WikiPageGenerator):
    """Generates the settlement list page for the wiki window."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("settlement_list.jinja")

        settlement_list: list[Any] = []

        for uid, (settlement, _) in sim.world.get_components((Settlement, Active)):
            settlement_list.append({"uid": uid, "name": settlement.gameobject.name})

        content = template.render(settlements=settlement_list)
        content = content.replace("\n", "")
        return content


class ClanListPageGenerator(WikiPageGenerator):
    """Generates the clan list page for the wiki window."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("clan_list.jinja")

        clan_list: list[Any] = []

        for uid, (clan, _) in sim.world.get_components((Clan, Active)):
            clan_list.append({"uid": uid, "name": clan.gameobject.name})

        content = template.render(clans=clan_list)
        content = content.replace("\n", "")
        return content


class FamilyListPageGenerator(WikiPageGenerator):
    """Generates the family list page for the wiki window."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("family_list.jinja")
        family_list: list[Any] = []

        for uid, (family, _) in sim.world.get_components((Family, Active)):
            family_list.append({"uid": uid, "name": family.gameobject.name})

        content = template.render(families=family_list)
        content = content.replace("\n", "")
        return content


class CharacterListPageGenerator(WikiPageGenerator):
    """Generates the family list page for the wiki window."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("character_list.jinja")
        character_list: list[Any] = []

        for uid, (character, _) in sim.world.get_components((Character, Active)):
            character_list.append({"uid": uid, "name": character.gameobject.name})

        content = template.render(characters=character_list)
        content = content.replace("\n", "")
        return content


class SettlementPageGenerator(WikiPageGenerator):
    """Generate page for a settlement."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("settlement.jinja")
        settlement: GameObject = kwargs["settlement"]

        content = template.render(
            settlement=settlement.get_component(Settlement),
            happiness=settlement.get_component(PopulationHappiness).value,
        )

        return content


class CharacterPageGenerator(WikiPageGenerator):
    """Generate page for a character."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("character.jinja")
        character: GameObject = kwargs["character"]

        content = template.render(character=character)

        return content


class FamilyPageGenerator(WikiPageGenerator):
    """Generate page for a family."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("family.jinja")
        family: GameObject = kwargs["family"]

        content = template.render(family=family)

        return content


class ClanPageGenerator(WikiPageGenerator):
    """Generate page for a clan."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("clan.jinja")
        clan: GameObject = kwargs["clan"]

        content = template.render(clan=clan.get_component(Clan))

        return content


class GameObjectPageGenerator(WikiPageGenerator):
    """Generates the family list page for the wiki window."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        uid = int(kwargs["uid"][0])
        gameobject = sim.world.gameobjects.get_gameobject(uid)
        object_type = gameobject.metadata["object_type"]

        if object_type == "settlement":
            content = SettlementPageGenerator().generate_page(
                sim, settlement=gameobject
            )
        elif object_type == "character":
            content = CharacterPageGenerator().generate_page(sim, character=gameobject)
        elif object_type == "clan":
            content = ClanPageGenerator().generate_page(sim, clan=gameobject)
        elif object_type == "family":
            content = FamilyPageGenerator().generate_page(sim, family=gameobject)
        else:
            content = f'<font size="6"><b>{gameobject.name} ({uid})</b></font>'

        content = content.replace("\n", "")
        return content


_page_generators: dict[str, WikiPageGenerator] = {
    "/index": IndexPageGenerator(),
    "/character_list": CharacterListPageGenerator(),
    "/settlement_list": SettlementListPageGenerator(),
    "/family_list": FamilyListPageGenerator(),
    "/clan_list": ClanListPageGenerator(),
    "/gameobject": GameObjectPageGenerator(),
}


class WikiWindow(UIWindow):
    """A window that displays information about all the characters."""

    def __init__(self, manager: UIManager, sim: Simulation):
        super().__init__(
            pygame.Rect((200, 50), (420, 520)),
            manager,
            window_display_title="Minerva World Wiki",
            resizable=True,
            object_id="#wiki_window",
        )
        self.sim = sim
        search_bar_top_margin = 2
        search_bar_bottom_margin = 2
        self.search_box = UITextEntryLine(
            pygame.Rect((150, search_bar_top_margin), (230, 30)),
            manager=manager,
            container=self,
            parent_element=self,
        )

        self.search_label = UILabel(
            pygame.Rect(
                (90, search_bar_top_margin),
                (56, self.search_box.rect.height),  # type: ignore
            ),
            "Search:",
            manager=manager,
            container=self,
            parent_element=self,
        )

        self.home_button = UIButton(
            pygame.Rect((20, search_bar_top_margin), (29, 29)),
            "",
            manager=manager,
            container=self,
            parent_element=self,
            object_id="#home_button",
        )

        self.remaining_window_size: tuple[int, int] = (
            self.get_container().get_size()[0],
            (
                self.get_container().get_size()[1]
                - (
                    self.search_box.rect.height  # type: ignore
                    + search_bar_top_margin
                    + search_bar_bottom_margin
                )
            ),
        )
        self.page_y_start_pos: int = (
            self.search_box.rect.height  # type: ignore
            + search_bar_top_margin
            + search_bar_bottom_margin
        )
        self.page_display = UITextBox(
            "",
            pygame.Rect(
                (0, self.page_y_start_pos),  # type: ignore
                self.remaining_window_size,
            ),
            manager=manager,
            container=self,
            parent_element=self,
            # pre_parsing_enabled=False,
        )
        self.set_page("/index")

    def process_event(self, event: pygame.event.Event):
        handled = super().process_event(event)

        if event.type == UI_TEXT_BOX_LINK_CLICKED:
            self.set_page(event.link_target)
            handled = True

        if event.type == UI_TEXT_ENTRY_FINISHED and event.ui_element == self.search_box:
            # results = self.search_pages(event.text)
            # self.create_search_results_page(results)
            # self.open_new_page("results")
            handled = True

        if (
            event.type == UI_BUTTON_PRESSED
            and event.ui_object_id == "#wiki_window.#home_button"
        ):
            self.set_page("/index")
            handled = True

        return handled

    def set_page(self, uri: str) -> None:
        """Sets the current page to display in the wiki window."""

        uri_data = urlparse(uri)
        page_params = parse_qs(uri_data.query)
        generator_path = uri_data.path

        content = _page_generators[generator_path].generate_page(
            self.sim, **page_params
        )

        self.page_display.kill()
        self.page_display = UITextBox(
            content,
            pygame.Rect((0, self.page_y_start_pos), self.remaining_window_size),
            manager=self.ui_manager,
            container=self,
            parent_element=self,
            # pre_parsing_enabled=False,
        )

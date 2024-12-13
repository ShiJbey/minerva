"""PyGame Minerva World Wiki Explorer."""

import pathlib
from abc import ABC, abstractmethod
from typing import Any, ClassVar
from urllib.parse import parse_qs, urlparse

import pygame
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pygame_gui import UI_TEXT_BOX_LINK_CLICKED
from pygame_gui.elements import UIButton, UITextBox, UIWindow
from pygame_gui.ui_manager import UIManager

from minerva.characters.components import Character, Family
from minerva.ecs import Active, Entity
from minerva.simulation import Simulation
from minerva.world_map.components import PopulationHappiness, Territory


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


class TerritoryListPageGenerator(WikiPageGenerator):
    """Generates the territory list page for the wiki window."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("territory_list.jinja")

        territory_list: list[Any] = []

        for uid, (territory, _) in sim.world.query_components((Territory, Active)):
            territory_list.append({"uid": uid, "name": territory.entity.name})

        content = template.render(territories=territory_list)
        content = content.replace("\n", "")
        return content


class FamilyListPageGenerator(WikiPageGenerator):
    """Generates the family list page for the wiki window."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("family_list.jinja")
        family_list: list[Any] = []

        for uid, (family, _) in sim.world.query_components((Family, Active)):
            family_list.append({"uid": uid, "name": family.entity.name})

        content = template.render(families=family_list)
        content = content.replace("\n", "")
        return content


class CharacterListPageGenerator(WikiPageGenerator):
    """Generates the family list page for the wiki window."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("character_list.jinja")
        character_list: list[Any] = []

        for uid, (character, _) in sim.world.query_components((Character, Active)):
            character_list.append({"uid": uid, "name": character.entity.name})

        content = template.render(characters=character_list)
        content = content.replace("\n", "")
        return content


class TerritoryPageGenerator(WikiPageGenerator):
    """Generate page for a territory."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("territory.jinja")
        territory: Entity = kwargs["territory"]

        content = template.render(
            territory=territory.get_component(Territory),
            happiness=territory.get_component(PopulationHappiness).value,
        )

        return content


class CharacterPageGenerator(WikiPageGenerator):
    """Generate page for a character."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("character.jinja")
        character: Entity = kwargs["character"]

        character_component = character.get_component(Character)

        content = template.render(character=character_component)

        return content


class FamilyPageGenerator(WikiPageGenerator):
    """Generate page for a family."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        template = _jinja_env.get_template("family.jinja")
        family: Entity = kwargs["family"]

        content = template.render(family=family.get_component(Family))

        return content


class EntityPageGenerator(WikiPageGenerator):
    """Generates the family list page for the wiki window."""

    def generate_page(self, sim: Simulation, **kwargs: Any) -> str:
        uid = int(kwargs["uid"][0])
        entity = sim.world.get_entity(uid)

        if entity.has_component(Territory):
            content = TerritoryPageGenerator().generate_page(sim, territory=entity)
        elif entity.has_component(Character):
            content = CharacterPageGenerator().generate_page(sim, character=entity)
        elif entity.has_component(Family):
            content = FamilyPageGenerator().generate_page(sim, family=entity)
        else:
            content = f'<font size="6"><b>{entity.name} ({uid})</b></font>'

        content = content.replace("\n", "")
        return content


_page_generators: dict[str, WikiPageGenerator] = {
    "/index": IndexPageGenerator(),
    "/character_list": CharacterListPageGenerator(),
    "/territory_list": TerritoryListPageGenerator(),
    "/family_list": FamilyListPageGenerator(),
    "/entity": EntityPageGenerator(),
}


class WikiWindow(UIWindow):
    """A window that displays information about all the characters."""

    TOOLBAR_HEIGHT: ClassVar[int] = 30
    TOOLBAR_PADDING_TOP: ClassVar[int] = 6
    TOOLBAR_PADDING_BOTTOM: ClassVar[int] = 6
    WINDOW_WIDTH: ClassVar[int] = 420
    WINDOW_HEIGHT: ClassVar[int] = 520

    def __init__(self, manager: UIManager, sim: Simulation) -> None:
        super().__init__(
            pygame.Rect((200, 50), (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)),
            manager,
            window_display_title="Minerva World Wiki",
            resizable=False,
            object_id="#wiki_window",
        )
        self.sim = sim
        # self.search_box = UITextEntryLine(
        #     pygame.Rect((150, search_bar_top_margin), (230, 30)),
        #     manager=manager,
        #     container=self,
        #     parent_element=self,
        # )
        #
        # self.search_label = UILabel(
        #     pygame.Rect(
        #         (90, search_bar_top_margin),
        #         (56, self.search_box.rect.height),  # type: ignore
        #     ),
        #     "Search:",
        #     manager=manager,
        #     container=self,
        #     parent_element=self,
        # )

        self.home_button = UIButton(
            pygame.Rect((20, self.TOOLBAR_PADDING_TOP), (32, 32)),
            "",
            manager=manager,
            container=self,
            parent_element=self,
            object_id="#home_button",
            command=self.go_home,
        )

        self.back_button = UIButton(
            pygame.Rect((60, self.TOOLBAR_PADDING_TOP), (32, 32)),
            "",
            manager=manager,
            container=self,
            parent_element=self,
            object_id="#back_button",
            command=self.go_back,
        )

        self.forward_button = UIButton(
            pygame.Rect((100, self.TOOLBAR_PADDING_TOP), (32, 32)),
            "",
            manager=manager,
            container=self,
            parent_element=self,
            object_id="#forward_button",
            command=self.go_forward,
        )

        self.remaining_window_size: tuple[int, int] = (
            self.get_container().get_size()[0],
            (
                self.get_container().get_size()[1]
                - (
                    self.TOOLBAR_HEIGHT
                    + self.TOOLBAR_PADDING_TOP
                    + self.TOOLBAR_PADDING_BOTTOM
                )
            ),
        )
        self.page_y_start_pos: int = (
            self.TOOLBAR_HEIGHT + self.TOOLBAR_PADDING_TOP + self.TOOLBAR_PADDING_BOTTOM
        )
        self.page_display = UITextBox(
            "",
            pygame.Rect(
                (0, self.page_y_start_pos),
                self.remaining_window_size,
            ),
            manager=manager,
            container=self,
            parent_element=self,
        )
        self.current_page: str = ""
        self.back_stack: list[str] = []
        self.forward_stack: list[str] = []
        self.go_home()

    def process_event(self, event: pygame.event.Event):
        handled = super().process_event(event)

        if event.type == UI_TEXT_BOX_LINK_CLICKED:
            self.back_stack.append(self.current_page)
            self.forward_stack.clear()
            self.go_to_page(event.link_target)
            handled = True

        return handled

    def go_home(self) -> None:
        """Go to the home page."""
        self.back_stack.clear()
        self.forward_stack.clear()
        self.go_to_page("/index")

    def go_forward(self) -> None:
        """Go forward a page."""
        destination = self.forward_stack.pop()
        self.back_stack.append(self.current_page)
        self.go_to_page(destination)

    def go_back(self) -> None:
        """Go to previous page."""
        destination = self.back_stack.pop()
        self.forward_stack.append(self.current_page)
        self.go_to_page(destination)

    def go_to_page(self, uri: str) -> None:
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
        )

        self.current_page = uri

        # Update forward and back button states
        if not self.back_stack:
            self.back_button.disable()
        else:
            self.back_button.enable()

        if not self.forward_stack:
            self.forward_button.disable()
        else:
            self.forward_button.enable()

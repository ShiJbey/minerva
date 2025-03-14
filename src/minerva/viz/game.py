"""Minerva PyGame Visualization."""

from __future__ import annotations

import pathlib

import pygame
import pygame.gfxdraw
import pygame_gui
import pygame_gui.elements.ui_panel
import pygame_gui.ui_manager

from minerva.characters.components import Dynasty, DynastyTracker
from minerva.simulation import Simulation
from minerva.simulation_events import SimulationEvents
from minerva.viz.camera import Camera
from minerva.viz.constants import TILE_SIZE
from minerva.viz.game_events import event_wiki_shown
from minerva.viz.tile_sprites import (
    BorderSprite,
    CastleSprite,
    CrownSprite,
    LabelSprite,
    TerrainType,
    get_terrain_tile,
)
from minerva.viz.utils import draw_text
from minerva.viz.wiki import WikiWindow
from minerva.world_map.components import CompassDir, Territory, WorldMap


class YSortCameraGroup(pygame.sprite.Group):  # type: ignore
    """This sprite group functions as a camera and sorts sprites by y-coordinate."""

    def __init__(
        self, display_surface: pygame.surface.Surface, speed: int = 10
    ) -> None:
        super().__init__()  # type: ignore
        self.display_surface = display_surface
        self.offset = pygame.math.Vector2(64, 64)
        self.speed = speed

    def custom_draw(self):
        """Draw the sprites in this group."""
        for sprite in sorted(self.sprites(), key=lambda s: s.rect.centery):  # type: ignore
            offset_pos = sprite.rect.topleft + self.offset  # type: ignore
            self.display_surface.blit(sprite.image, offset_pos)  # type: ignore

    def update(self, delta: pygame.math.Vector2) -> None:
        """Update the position of the camera."""
        self.offset += delta * self.speed


class Game:
    """An instance of a Minerva Game."""

    def __init__(self, simulation: Simulation) -> None:
        pygame.init()  # pylint: disable=no-member
        pygame.font.init()  # pylint: disable=no-member
        self.window_width = simulation.config.window_width
        self.window_height = simulation.config.window_height
        self.background_color = simulation.config.background_color
        self.show_debug = simulation.config.show_debug
        self.display = pygame.Surface((self.window_width, self.window_height))
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Minerva")
        self.fps = simulation.config.fps
        self.clock = pygame.time.Clock()
        self.is_running = False
        self.ui_manager = pygame_gui.ui_manager.UIManager(  # type: ignore
            (self.window_width, self.window_height),
            pathlib.Path(__file__).parent / "resources/themes/theme.json",
        )
        self.font = pygame.font.SysFont("Comic Sans MS", 12)
        self.simulation = simulation
        self.camera = Camera(self.window_width, self.window_height, 10)
        self.play_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((0, 0), (100, 50)),
            text="Play",
            manager=self.ui_manager,
            command=self.on_play_simulation,
        )
        self.pause_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((100, 0), (100, 50)),
            text="Pause",
            manager=self.ui_manager,
            command=self.on_pause_simulation,
        )
        self.pause_button.disable()
        self.sim_running = False
        self.sim_update_cooldown = 1.0 / simulation.config.sim_update_frequency
        self.arrow_key_states = {
            "left": False,
            "right": False,
            "up": False,
            "down": False,
        }
        self.ui_manager.preload_fonts(
            [
                {"name": "noto_sans", "point_size": 24, "style": "bold"},
                {"name": "noto_sans", "point_size": 24, "style": "bold_italic"},
                {"name": "noto_sans", "point_size": 18, "style": "bold"},
                {"name": "noto_sans", "point_size": 18, "style": "regular"},
                {"name": "noto_sans", "point_size": 18, "style": "bold_italic"},
                {"name": "noto_sans", "point_size": 14, "style": "bold"},
            ]
        )
        self.wiki_window = WikiWindow(self.ui_manager, self.simulation)
        self.wiki_window.kill()
        self.visible_sprites = YSortCameraGroup(self.display)
        self.terrain_tiles = YSortCameraGroup(self.display)
        self._castle_sprites: list[CastleSprite] = []

        self.register_game_event_listeners()
        self.register_simulation_event_listeners()

    def register_game_event_listeners(self):
        """Register callbacks for game events."""
        event_wiki_shown.add_listener(self._on_show_wiki)

    def register_simulation_event_listeners(self):
        """Register callbacks for simulation events."""
        sim_events = self.simulation.world.get_resource(SimulationEvents)

        sim_events.map_generated.add_listener(self._on_map_generated)

    def _on_map_generated(self, world_map: WorldMap) -> None:
        """Callback for when the map is generated."""
        self._create_terrain_sprites(world_map)
        self._create_border_sprites(world_map)
        self._create_castle_sprites(world_map)

    def on_play_simulation(self) -> None:
        """."""
        print("Simulation playing")
        self.play_button.disable()
        self.pause_button.enable()
        self.sim_running = True

    def on_pause_simulation(self) -> None:
        """."""
        print("Simulation Paused")
        self.play_button.enable()
        self.pause_button.disable()
        self.sim_running = False

    def run(self) -> None:
        """Run the game."""
        self.is_running = True
        while self.is_running:
            time_delta = self.clock.tick(self.fps) / 1000.0
            self.handle_events()
            self.update(time_delta)
            self.draw()
        pygame.quit()  # pylint: disable=no-member

    def update(self, delta_time: float) -> None:
        """Update the active mode"""
        self.ui_manager.update(delta_time)  # type: ignore

        # Update the camera
        camera_delta = pygame.Vector2(0, 0)
        if self.arrow_key_states["up"]:
            camera_delta += pygame.Vector2(0, 1)
        if self.arrow_key_states["left"]:
            camera_delta += pygame.Vector2(1, 0)
        if self.arrow_key_states["down"]:
            camera_delta += pygame.Vector2(0, -1)
        if self.arrow_key_states["right"]:
            camera_delta += pygame.Vector2(-1, 0)
        self.camera.update(camera_delta)
        self.visible_sprites.update(camera_delta)
        self.terrain_tiles.update(camera_delta)

        # Update the simulation
        self.sim_update_cooldown -= delta_time
        if self.sim_update_cooldown <= 0 and self.sim_running:
            self.simulation.step()

    def draw_debug(self) -> None:
        """Draw debug information"""
        draw_text(
            self.display,
            f"FPS: {round(self.clock.get_fps())}",
            self.window_width - 36,
            self.window_height - 24,
            self.font,
        )

    def draw(self) -> None:
        """Draw the active game mode"""
        self.display.fill(self.background_color)

        self.terrain_tiles.custom_draw()

        self._draw_world_grid_lines(color="#ffffff")

        self.visible_sprites.custom_draw()

        self.ui_manager.draw_ui(self.display)  # type: ignore

        if self.show_debug:
            self.draw_debug()

        self.screen.blit(self.display, (0, 0))
        pygame.display.update()

    def _draw_world_grid_lines(self, color: str = "#000000") -> None:
        # Draw the ground
        # world_grid = self.simulation.world.get_resource(WorldGrid)
        if not self.simulation.world.has_resource(WorldMap):
            return

        world_map = self.simulation.world.get_resource(WorldMap)
        n_cols, n_rows = world_map.territory_grid.get_size()

        for y in range(n_rows + 1):
            for x in range(n_cols + 1):
                x1 = x * TILE_SIZE
                x2 = n_cols * TILE_SIZE
                y1 = y * TILE_SIZE
                y2 = n_rows * TILE_SIZE
                pygame.gfxdraw.hline(
                    self.display,
                    x1 + int(self.camera.scroll.x),
                    x2 + int(self.camera.scroll.x),
                    y1 + int(self.camera.scroll.y),
                    pygame.color.Color(color),
                )
                pygame.gfxdraw.vline(
                    self.display,
                    x1 + int(self.camera.scroll.x),
                    y1 + int(self.camera.scroll.y),
                    y2 + int(self.camera.scroll.y),
                    pygame.color.Color(color),
                )

    def _create_castle_sprites(self, world_map: WorldMap) -> None:
        dynasty_tracker = self.simulation.world.get_resource(DynastyTracker)
        royal_family = (
            dynasty_tracker.current_dynasty.get_component(Dynasty).family
            if dynasty_tracker.current_dynasty
            else None
        )

        for territory in world_map.territories:
            castle_sprite = CastleSprite(territory)
            castle_label = LabelSprite(
                text=territory.name,
                font=self.font,
                parent=castle_sprite,
            )

            territory_component = territory.get_component(Territory)
            if territory_component.controlling_family:

                if territory_component.controlling_family == royal_family:
                    crown_sprite = CrownSprite(castle_sprite)
                    self.visible_sprites.add(crown_sprite)  # type: ignore

                # family_component = (
                #     territory_component.controlling_family.get_component(Family)
                # )
                # if family_component.clan:
                #     clan_component = family_component.clan.get_component(Clan)
                #     flag_sprite.set_primary_color(
                #         pygame.color.Color(clan_component.color_primary)
                #     )
                #     flag_sprite.set_secondary_color(
                #         pygame.color.Color(clan_component.color_secondary)
                #     )

            self.visible_sprites.add(castle_sprite)  # type: ignore
            self.visible_sprites.add(castle_label)  # type: ignore
            self._castle_sprites.append(castle_sprite)

    def _create_border_sprites(self, world_map: WorldMap) -> None:
        for (x, y), wall_flags in world_map.borders.enumerate():

            if wall_flags == CompassDir.NONE:
                continue

            sprite = BorderSprite(
                (x * TILE_SIZE, y * TILE_SIZE),
                pygame.color.Color("blue"),
                pygame.color.Color("yellow"),
                wall_flags,
            )

            self.visible_sprites.add(sprite)  # type: ignore

    def _create_terrain_sprites(self, world_map: WorldMap) -> None:
        for (x, y), _ in world_map.territory_grid.enumerate():
            x1 = x * TILE_SIZE
            y1 = y * TILE_SIZE
            self.terrain_tiles.add(get_terrain_tile(TerrainType.GRASS, (x1, y1)))  # type: ignore

    def handle_events(self):
        """Active mode handles PyGame events"""
        for event in pygame.event.get():
            if self.ui_manager.process_events(event):  # type: ignore
                continue

            if event.type == pygame.constants.QUIT:
                self.is_running = False
                continue

            if event.type == pygame.constants.KEYDOWN:
                if event.key == pygame.constants.K_ESCAPE:
                    self.is_running = False
                    continue

            if (
                event.type == pygame.KEYDOWN
                and event.key == pygame.K_F1
                and not self.wiki_window.alive()
            ):
                self.wiki_window = WikiWindow(
                    manager=self.ui_manager, sim=self.simulation
                )

            if event.type == pygame.constants.KEYDOWN:
                if event.key == pygame.constants.K_UP:
                    self.arrow_key_states["up"] = True
                if event.key == pygame.constants.K_LEFT:
                    self.arrow_key_states["left"] = True
                if event.key == pygame.constants.K_DOWN:
                    self.arrow_key_states["down"] = True
                if event.key == pygame.constants.K_RIGHT:
                    self.arrow_key_states["right"] = True
                continue

            if event.type == pygame.constants.KEYUP:
                if event.key == pygame.constants.K_UP:
                    self.arrow_key_states["up"] = False
                if event.key == pygame.constants.K_LEFT:
                    self.arrow_key_states["left"] = False
                if event.key == pygame.constants.K_DOWN:
                    self.arrow_key_states["down"] = False
                if event.key == pygame.constants.K_RIGHT:
                    self.arrow_key_states["right"] = False
                if event.key == pygame.constants.K_SPACE:
                    if self.sim_running:
                        self.on_pause_simulation()
                    else:
                        self.on_play_simulation()
                continue

            if event.type == pygame.constants.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                adjusted_pos = (
                    pos[0] - int(self.visible_sprites.offset.x),
                    pos[1] - int(self.visible_sprites.offset.y),
                )

                for sprite in self._castle_sprites:
                    assert sprite.rect
                    sprite_rect = sprite.rect
                    if sprite_rect.collidepoint(adjusted_pos):
                        sprite.on_click()
                        break

    def _on_show_wiki(self, uid: int):

        if not self.wiki_window.alive():
            self.wiki_window = WikiWindow(manager=self.ui_manager, sim=self.simulation)

        self.wiki_window.go_to_page(f"/entity?uid={uid}")

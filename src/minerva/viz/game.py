"""Minerva PyGame Visualization."""

from __future__ import annotations

import pathlib

import pygame
import pygame.gfxdraw
import pygame_gui
import pygame_gui.elements.ui_panel
import pygame_gui.ui_manager

from minerva.constants import (
    BACKGROUND_COLOR,
    CAMERA_SPEED,
    FPS,
    SHOW_DEBUG,
    SIM_UPDATE_FREQ,
    TILE_SIZE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from minerva.simulation import Simulation
from minerva.viz.camera import Camera
from minerva.viz.tile_sprites import (
    CastleSprite,
    TerrainType,
    get_terrain_tile,
    get_wall_spite,
)
from minerva.viz.utils import draw_text
from minerva.viz.wiki import WikiWindow
from minerva.world_map.components import WorldMap


class YSortCameraGroup(pygame.sprite.Group):  # type: ignore
    """This sprite group functions as a camera and sorts sprites by y-coordinate."""

    def __init__(self, display_surface: pygame.surface.Surface) -> None:
        super().__init__()  # type: ignore
        self.display_surface = display_surface
        self.offset = pygame.math.Vector2(64, 64)
        self.speed = CAMERA_SPEED

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
        self.display = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Minerva")
        self.clock = pygame.time.Clock()
        self.is_running = False
        self.ui_manager = pygame_gui.ui_manager.UIManager(  # type: ignore
            (WINDOW_WIDTH, WINDOW_HEIGHT),
            pathlib.Path(__file__).parent / "resources/themes/theme.json",
        )
        self.font = pygame.font.SysFont("Comic Sans MS", 12)
        self.simulation = simulation
        self.camera = Camera(WINDOW_WIDTH, WINDOW_HEIGHT, 10)
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
        self.sim_initialized = False
        self.sim_update_cooldown = 1.0 / SIM_UPDATE_FREQ
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
        self.world_map = simulation.world.resources.get_resource(WorldMap)
        self._create_terrain_sprites()
        self._create_border_sprites()
        self._create_castle_sprites()

    def on_play_simulation(self) -> None:
        """."""
        print("Simulation playing")
        self.play_button.disable()
        self.pause_button.enable()
        self.sim_running = True
        self.sim_initialized = True

    def on_pause_simulation(self) -> None:
        """."""
        print("Simulation Paused")
        self.play_button.enable()
        self.pause_button.disable()
        self.sim_running = False

    def run(self) -> None:
        """Run the game."""
        self.is_running = True
        self.simulation.initialize_content()
        while self.is_running:
            time_delta = self.clock.tick(FPS) / 1000.0
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
        # self.sim_update_cooldown -= delta_time
        # if (
        #     # self.sim_update_cooldown <= 0 and
        #     self.sim_running
        #     and not self.world_grid_generator.is_complete
        # ):
        #     # self.world_grid_generator.generate_territories()
        #     # self.simulation.step()
        #     # self.world_grid_generator.step()
        #     #
        #     # if self.world_grid_generator.is_complete:
        #     #     self._create_border_sprites()

    def draw_debug(self) -> None:
        """Draw debug information"""
        draw_text(
            self.display,
            f"FPS: {round(self.clock.get_fps())}",
            WINDOW_WIDTH - 36,
            WINDOW_HEIGHT - 24,
            self.font,
        )

    def draw(self) -> None:
        """Draw the active game mode"""
        self.display.fill(BACKGROUND_COLOR)

        self.terrain_tiles.custom_draw()

        self._draw_world_grid_lines(color="#ffffff")

        self.visible_sprites.custom_draw()

        self.ui_manager.draw_ui(self.display)  # type: ignore

        if SHOW_DEBUG:
            self.draw_debug()

        self.screen.blit(self.display, (0, 0))
        pygame.display.update()

    def _draw_world_grid_lines(self, color: str = "#000000") -> None:
        # Draw the ground
        # world_grid = self.simulation.world.resources.get_resource(WorldGrid)

        n_cols, n_rows = self.world_map.territory_grid.get_size()

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

    def _create_castle_sprites(self) -> None:
        for settlement in self.world_map.settlements:
            self.visible_sprites.add(CastleSprite(settlement))  # type: ignore

    def _create_border_sprites(self) -> None:
        for (x, y), wall_flags in self.world_map.borders.enumerate():
            sprite = get_wall_spite((x * TILE_SIZE, y * TILE_SIZE), wall_flags)
            if sprite is not None:
                self.visible_sprites.add(sprite)  # type: ignore

    def _create_terrain_sprites(self) -> None:
        for (x, y), _ in self.simulation.world.resources.get_resource(
            WorldMap
        ).territory_grid.enumerate():
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

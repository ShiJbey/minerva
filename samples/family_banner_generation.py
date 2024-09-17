"""PyGame sample that visualizes all the family banner combinations.

"""

from __future__ import annotations

import pygame
import pygame.gfxdraw

from minerva.constants import (
    CAMERA_SPEED,
    CLAN_COLORS_PRIMARY,
    CLAN_COLORS_SECONDARY,
    FAMILY_BANNER_SHAPES,
    FAMILY_COLORS_TERTIARY,
    FPS,
    TILE_SIZE,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from minerva.viz.family_banners import FamilyBannerSprite


class YSortCameraGroup(pygame.sprite.Group):  # type: ignore
    """This sprite group functions as a camera and sorts sprites by y-coordinate."""

    __slots__ = ("display_surface", "offset", "speed")

    def __init__(self, display_surface: pygame.surface.Surface, speed: int = 0) -> None:
        super().__init__()  # type: ignore
        self.display_surface = display_surface
        self.offset = pygame.math.Vector2(64, 64)
        self.speed = speed if speed else CAMERA_SPEED

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

    __slots__ = (
        "display",
        "screen",
        "clock",
        "is_running",
        "font",
        "arrow_key_states",
        "family_banners",
    )

    def __init__(self) -> None:
        pygame.init()  # pylint: disable=no-member
        pygame.font.init()  # pylint: disable=no-member
        self.display = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Minerva")
        self.clock = pygame.time.Clock()
        self.is_running = False
        self.font = pygame.font.SysFont("Comic Sans MS", 12)
        self.arrow_key_states = {
            "left": False,
            "right": False,
            "up": False,
            "down": False,
        }
        self.family_banners = YSortCameraGroup(self.display, 150)
        self._create_all_family_banners()

    def run(self) -> None:
        """Run the game."""
        self.is_running = True
        while self.is_running:
            delta_time = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(delta_time)
            self.draw()
        pygame.quit()  # pylint: disable=no-member

    def update(self, delta_time: float) -> None:
        """Update the active mode"""

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

        self.family_banners.update(camera_delta * delta_time)

    def draw(self) -> None:
        """Draw the active game mode"""
        self.display.fill("#999999")
        self.family_banners.custom_draw()
        self.screen.blit(self.display, (0, 0))
        pygame.display.update()

    def _create_all_family_banners(self, flags_per_row: int = 50) -> None:
        """Create all family flags and tile them on the map."""
        flags_in_row: int = 0
        current_row: int = 0

        for color_primary in CLAN_COLORS_PRIMARY:
            for color_secondary in CLAN_COLORS_SECONDARY:
                for color_tertiary in FAMILY_COLORS_TERTIARY:
                    for shape_0 in FAMILY_BANNER_SHAPES:

                        x = (TILE_SIZE + 4) * flags_in_row
                        y = (TILE_SIZE + 4) * current_row

                        FamilyBannerSprite(
                            x,
                            y,
                            color_primary,
                            color_secondary,
                            color_tertiary,
                            shape_0,
                            self.family_banners,
                        )

                        flags_in_row += 1

                        if flags_in_row == flags_per_row:
                            flags_in_row = 0
                            current_row += 1

    def handle_events(self):
        """Active mode handles PyGame events"""
        for event in pygame.event.get():
            if event.type == pygame.constants.QUIT:
                self.is_running = False
                continue

            if event.type == pygame.constants.KEYDOWN:
                if event.key == pygame.constants.K_ESCAPE:
                    self.is_running = False
                    continue

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


if __name__ == "__main__":

    game = Game()
    game.run()

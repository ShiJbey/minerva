"""Minerva Constants."""

# === pygame settings

WINDOW_WIDTH: int = 1280
"""Width of the game window in pixels (16:9 Aspect ratio)."""
WINDOW_HEIGHT: int = 720
"""Height of the game window inf pixels (16:9 Aspect ratio)."""
FPS: int = 60
"""Desired frames per second."""
SHOW_DEBUG: bool = False
"""Display debug outputs."""
SIM_UPDATE_FREQ: int = 12
"""Number of simulation steps per second."""
BACKGROUND_COLOR = "#42ACAF"
"""Background color of the pygame window."""
CAMERA_SPEED = 10
"""Panning speed of the camera."""
TILE_SIZE = 32
"""The size of the game tile grid."""
SETTLEMENT_BORDER_WIDTH = 1
"""Pixel width of the border."""
SETTLEMENT_BORDER_PADDING = 0
"""Padding between edge of tile and border line."""

# === Character Settings ===

CHARACTER_MOTIVE_MAX = 100
CHARACTER_MOTIVE_BASE = 50

BEHAVIOR_UTILITY_THRESHOLD = 0

# === Clan/Family Settings ===

MAX_ADVISORS_PER_FAMILY = 3
MAX_WARRIORS_PER_FAMILY = 3

CLAN_COLORS_PRIMARY = [
    "#01161E",  # Rich Black
    "#124559",  # Midnight Green
    "#598392",  # Air Force Blue
    "#AEC3B0",  # Ash Grey
    "#654236",  # Liver
]

CLAN_COLORS_SECONDARY = [
    "#e90000",  # red
    "#31d5c8",  # light blue
    "#a538c6",  # violet
    "#05fb00",  # green
    "#001eba",  # royal blue
]

FAMILY_COLORS_TERTIARY = [
    "#FF338C",  # Crimson
    "#33FF57",  # Bittersweet
    "#ffffff",  # Orange
    "#FB62F6",  # Pink
    "#fff500",  # Yellow
]

FAMILY_BANNER_SHAPES = [
    "circle",
    "square",
    "diamond",
    "triangle_up",
    "triangle_down",
]

# === Territory Settings ===

MIN_POLITICAL_INFLUENCE = 0
MAX_POLITICAL_INFLUENCE = 100
BASE_SETTLEMENT_HAPPINESS = 50
MIN_SETTLEMENT_HAPPINESS = 0
MAX_SETTLEMENT_HAPPINESS = 100

TERRITORY_GENERATION_DEBUG_COLORS = [
    "#e90000",  # red
    "#31d5c8",  # light blue
    "#a538c6",  # violet
    "#cccccc",  # grey
    "#33a7c8",  # darker blue
    "#FF5733",  # (Bright Orange)
    "#33FF57",  # (Lime Green)
    "#FF338C",  # (Crimson)
    "#FFD733",  # (Bright Yellow)
    "#33FFF3",  # (Cyan)
    "#8C33FF",  # (Purple)
    "#FFB833",  # (Amber)
    "#05fb00",  # green
    "#001eba",  # royal blue
    "#fff500",  # yellow
    "#33FF8C",  # (Mint Green)
    "#FF3333",  # (Bright Red)
    "#33A6FF",  # (Sky Blue)
    "#FF3380",  # (Magenta)
    "#FFC733",  # (Gold)
    "#3380FF",  # (Royal Blue)
    "#FF8333",  # (Coral)
    "#33FF33",  # (Neon Green)
    "#33FFB8",  # (Light Green)
]

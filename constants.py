# Bildschirm
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Excavate Game"

# Tile-Größe in Pixeln
TILE_SIZE = 32

# Welt-Größe in Tiles
WORLD_WIDTH = 30
WORLD_HEIGHT = 120

# Zonen (Tiefe in Tiles)
ZONES = [
    {"name": "Erde",         "from": 0,   "to": 10,  "hardness": 1, "color": (139, 90,  43)},
    {"name": "Bruchstein",   "from": 10,  "to": 35,  "hardness": 2, "color": (120, 120, 120)},
    {"name": "Fester Stein", "from": 35,  "to": 65,  "hardness": 3, "color": (80,  80,  80)},
    {"name": "Granit",       "from": 65,  "to": 95,  "hardness": 4, "color": (60,  50,  70)},
    {"name": "Obsidian",     "from": 95,  "to": 120, "hardness": 5, "color": (20,  10,  30)},
]

# Upgrade-Schwellen (Punkte zum Erreichen des nächsten Pickaxe-Levels)
UPGRADE_THRESHOLDS = [0, 50, 150, 350, 700]

# Ressourcen: (name, points, color, probability_per_zone)
# probability_per_zone: Liste mit Wahrscheinlichkeit (0.0-1.0) für jede Zone
RESOURCES = {
    "kohle":   {"points": 5,   "color": (40,  40,  40),   "prob": [0.20, 0.25, 0.10, 0.05, 0.00]},
    "eisen":   {"points": 15,  "color": (180, 140, 100),  "prob": [0.00, 0.12, 0.15, 0.08, 0.02]},
    "smaragd": {"points": 40,  "color": (0,   200, 80),   "prob": [0.00, 0.00, 0.05, 0.05, 0.03]},
    "rubin":   {"points": 80,  "color": (220, 30,  30),   "prob": [0.00, 0.00, 0.00, 0.03, 0.03]},
    "saphir":  {"points": 100, "color": (30,  80,  220),  "prob": [0.00, 0.00, 0.00, 0.01, 0.02]},
}

# Höhlen: Anteil der Welt der als Höhlen generiert wird
CAVE_COUNT = 8
CAVE_MIN_SIZE = 3
CAVE_MAX_SIZE = 8

# Farben
COLOR_SKY        = (100, 160, 220)
COLOR_AIR        = (0,   0,   0,   0)   # transparent / leer
COLOR_WATER      = (30,  100, 200)
COLOR_LAVA       = (220, 80,  0)
COLOR_PLAYER     = (255, 220, 50)
COLOR_HUD_BG     = (0,   0,   0)
COLOR_HUD_TEXT   = (255, 255, 255)
COLOR_WHITE      = (255, 255, 255)
COLOR_BLACK      = (0,   0,   0)
COLOR_UPGRADE    = (255, 215, 0)

# Spieler
PLAYER_SPEED     = 4        # Pixel pro Frame
PLAYER_JUMP      = -12      # Anfangsgeschwindigkeit beim Springen
GRAVITY          = 0.5
MAX_FALL_SPEED   = 12
PLAYER_WIDTH     = 24
PLAYER_HEIGHT    = 28
PLAYER_MAX_HP    = 5

# Schaden
WATER_DAMAGE_INTERVAL = 60  # Frames zwischen Wasser-Schaden
LAVA_DAMAGE            = 5  # Sofort-Tod (ganzes HP)

# Kamera
CAMERA_LAG = 0.1  # Wie schnell die Kamera folgt (0=sofort, 1=nie)

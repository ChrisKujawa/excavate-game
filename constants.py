# Bildschirm
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
TITLE = "Excavate Game"

# Tile-Größe in Pixeln
TILE_SIZE = 32

# Welt-Größe in Tiles
WORLD_HEIGHT = 200          # Tiefe der Welt
WORLD_INITIAL_WIDTH = 50    # Startbreite (zentriert um x=0)
WORLD_EXPAND_THRESHOLD = 20 # Spalten Abstand zum Rand bevor expandiert wird
WORLD_EXPAND_AMOUNT = 30    # Neue Spalten pro Expansion

# Zonen (Tiefe in Tiles) – 9 Schichten
ZONES = [
    {"name": "Erde",            "from": 0,   "to": 10,  "hardness": 1, "color": (139, 90,  43)},
    {"name": "Bruchstein",      "from": 10,  "to": 30,  "hardness": 2, "color": (120, 120, 120)},
    {"name": "Fester Stein",    "from": 30,  "to": 60,  "hardness": 3, "color": (80,  80,  80)},
    {"name": "Granit",          "from": 60,  "to": 90,  "hardness": 4, "color": (60,  50,  70)},
    {"name": "Obsidian",        "from": 90,  "to": 120, "hardness": 5, "color": (20,  10,  30)},
    {"name": "Basalt",          "from": 120, "to": 150, "hardness": 6, "color": (45,  35,  55)},
    {"name": "Quarz",           "from": 150, "to": 170, "hardness": 7, "color": (210, 200, 225)},
    {"name": "Tiefer Kristall", "from": 170, "to": 190, "hardness": 8, "color": (80,  170, 200)},
    {"name": "Urkern",          "from": 190, "to": 200, "hardness": 9, "color": (5,   3,   20)},
]

# Upgrade-Schwellen (Punkte zum Erreichen des nächsten Pickaxe-Levels)
UPGRADE_THRESHOLDS = [0, 50, 150, 350, 700, 1200, 2000, 3000, 5000]

# Ressourcen: (name, points, color, probability_per_zone)
# probability_per_zone: Liste mit Wahrscheinlichkeit pro Zone (eine Eintraag pro Zone oben)
RESOURCES = {
    "kohle":    {"points": 5,    "color": (40,  40,  40),  "prob": [0.20, 0.25, 0.10, 0.05, 0.00, 0.00, 0.00, 0.00, 0.00]},
    "eisen":    {"points": 15,   "color": (180, 140, 100), "prob": [0.00, 0.12, 0.15, 0.08, 0.02, 0.00, 0.00, 0.00, 0.00]},
    "smaragd":  {"points": 40,   "color": (0,   200, 80),  "prob": [0.00, 0.00, 0.05, 0.05, 0.03, 0.00, 0.00, 0.00, 0.00]},
    "rubin":    {"points": 80,   "color": (220, 30,  30),  "prob": [0.00, 0.00, 0.00, 0.03, 0.03, 0.02, 0.00, 0.00, 0.00]},
    "saphir":   {"points": 100,  "color": (30,  80,  220), "prob": [0.00, 0.00, 0.00, 0.01, 0.02, 0.02, 0.01, 0.00, 0.00]},
    "gold":     {"points": 150,  "color": (255, 200, 0),   "prob": [0.00, 0.00, 0.00, 0.00, 0.02, 0.04, 0.03, 0.01, 0.00]},
    "platin":   {"points": 250,  "color": (200, 220, 240), "prob": [0.00, 0.00, 0.00, 0.00, 0.00, 0.02, 0.03, 0.02, 0.01]},
    "opal":     {"points": 400,  "color": (255, 160, 210), "prob": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.02, 0.03, 0.02]},
    "amethyst": {"points": 600,  "color": (150, 50,  200), "prob": [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.02, 0.03]},
}

# Höhlen
CAVE_COUNT = 10       # pro WORLD_INITIAL_WIDTH Spalten
CAVE_MIN_SIZE = 3
CAVE_MAX_SIZE = 9

# Farben
COLOR_SKY        = (100, 160, 220)
COLOR_WATER      = (30,  100, 200)
COLOR_LAVA       = (220, 80,  0)
COLOR_PLAYER     = (255, 220, 50)
COLOR_HUD_BG     = (0,   0,   0)
COLOR_HUD_TEXT   = (255, 255, 255)
COLOR_WHITE      = (255, 255, 255)
COLOR_BLACK      = (0,   0,   0)
COLOR_UPGRADE    = (255, 215, 0)

# Spieler
PLAYER_SPEED     = 4
PLAYER_JUMP      = -12
GRAVITY          = 0.5
MAX_FALL_SPEED   = 12
PLAYER_WIDTH     = 24
PLAYER_HEIGHT    = 28
PLAYER_MAX_HP    = 5

# Schaden
WATER_DAMAGE_INTERVAL = 60
LAVA_DAMAGE            = 5

# Kamera
CAMERA_LAG = 0.1

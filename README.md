# 🪨 Excavate Game

Ein 2D Side-View Graber-Spiel in Python + Pygame. Steuere **TEC** durch verschiedene Gesteinsschichten, sammle Ressourcen und finde den riesigen Diamanten am Boden der Welt!

> **TEC** steht für die Anfangsbuchstaben unserer Entwickler-Familie: **T**, **E** und **C** 💛

## Spielziel

Starte an der Oberfläche und grabe dich immer tiefer. Sammle Punkte, upgrade deine Spitzhacke und finde den **Riesigen Diamanten** tief im Obsidian-Gestein. Die Welt ist unendlich breit – erforsche sie nach links und rechts!

## Steuerung

| Taste | Aktion |
|-------|--------|
| `← →` | Bewegen (gegen Wand = graben) |
| `↑` / `SPACE` | Springen |
| `↓` / `S` | Nach unten graben |
| `Q` | Links graben |
| `E` | Rechts graben |
| `R` | Neustart |
| `ESC` | Beenden |

## Tiefen-Zonen

| Zone | Tiefe | Material | Pickaxe |
|------|-------|----------|---------|
| 🟫 | 0–10 | Erde | Lv 1 |
| ⬛ | 10–30 | Bruchstein | Lv 2 |
| 🔲 | 30–60 | Fester Stein | Lv 3 |
| 🟪 | 60–90 | Granit | Lv 4 |
| ⚫ | 90–120 | Obsidian | Lv 5 |
| 🔵 | 120–150 | Basalt | Lv 6 |
| ⬜ | 150–170 | Quarz | Lv 7 |
| 💎 | 170–190 | Tiefer Kristall | Lv 8 |
| 🌑 | 190–200 | Urkern | Lv 9 |

## Ressourcen & Punkte

| Ressource | Punkte | Wo |
|-----------|--------|----|
| 🖤 Kohle | 5 | Erde / Bruchstein |
| 🟤 Eisen | 15 | Bruchstein / Fester Stein |
| 💚 Smaragd | 40 | Fester Stein / Granit |
| ❤️ Rubin | 80 | Granit / Obsidian |
| 💙 Saphir | 100 | Obsidian / Basalt |
| 🟡 Gold | 150 | Obsidian / Basalt |
| 🩶 Platin | 250 | Basalt / Quarz |
| 🩷 Opal | 400 | Quarz / Tiefer Kristall |
| 💜 Amethyst | 600 | Tiefer Kristall / Urkern |
| 🦴 **Fossil** | **1000** | **Quarz bis Urkern (sehr selten!)** |
| 💎 Riesdiamant | WIN | 1× am Boden |

## Pickaxe-Upgrades

| Punkte | Level |
|--------|-------|
| 50 | Lv 2 |
| 150 | Lv 3 |
| 350 | Lv 4 |
| 700 | Lv 5 |
| 1200 | Lv 6 |
| 2000 | Lv 7 |
| 3000 | Lv 8 |
| 5000 | Lv 9 |

## Gefahren

- 💧 **Wasser-Höhlen** – langsamer HP-Verlust. Wasser fließt nach unten!
- 🔥 **Lava-Höhlen** – sofortiger Tod. Lava fließt nach unten!
- Leere Höhlen: harmlos, aber man fällt rein!

## Installation & Starten

```bash
pip install pygame-ce
python main.py
```

## Tests ausführen

```bash
python -m pytest tests/ -v
```

## Projektstruktur

```
excavate-game/
├── main.py         # Einstiegspunkt
├── game.py         # Spielschleife + Zustände
├── world.py        # Prozedurale & expandierbare Welt-Generierung
├── player.py       # TEC – Spieler-Logik
├── tile.py         # Tile-Typen
├── camera.py       # Kamera (vertikal + horizontal)
├── ui.py           # HUD, Start-Screen, Game-Over/Win-Screens
├── highscore.py    # Lokale Bestenliste (Top 5)
├── constants.py    # Alle Konstanten
└── tests/          # 93 Pytest Tests
```


Game build with my kids

# 🪨 Excavate Game

Ein 2D Side-View Graber-Spiel in Python + Pygame. Grab dich durch verschiedene Gesteinsschichten, sammle Ressourcen, upgrade deine Ausrüstung und finde den riesigen Diamanten am Boden!

## Spielziel

Starte an der Oberfläche und grabe dich immer tiefer. Sammle Punkte durch Ressourcen, verbessere deine Spitzhacke und finde den **Riesigen Diamanten** im Obsidian-Tiefgestein.

## Steuerung

| Taste | Aktion |
|-------|--------|
| `← →` | Bewegen |
| `↑` / `SPACE` | Springen |
| `↓` / `S` | Nach unten graben |
| `Q` | Links graben |
| `E` | Rechts graben |
| `R` | Neustart |
| `ESC` | Beenden |

## Tiefen-Zonen

| Zone | Tiefe | Material | Benötigt |
|------|-------|----------|----------|
| 🟫 | 0–10 | Erde | Lv 1 |
| ⬛ | 10–35 | Bruchstein | Lv 2 |
| 🔲 | 35–65 | Fester Stein | Lv 3 |
| 🟪 | 65–95 | Granit | Lv 4 |
| ⚫ | 95–120 | Obsidian | Lv 5 |

## Ressourcen

| Ressource | Punkte | Vorkommen |
|-----------|--------|-----------|
| 🖤 Kohle | 5 | Häufig |
| 🟤 Eisen | 15 | Mittel |
| 💚 Smaragd | 40 | Selten |
| ❤️ Rubin | 80 | Sehr selten |
| 💙 Saphir | 100 | Sehr selten |
| 💎 Riesdiamant | WIN | 1× am Boden |

## Upgrade-Schwellen

| Punkte | Pickaxe-Level |
|--------|---------------|
| 50 | Lv 2 |
| 150 | Lv 3 |
| 350 | Lv 4 |
| 700 | Lv 5 |

## Gefahren

- 💧 **Wasser-Höhlen** – langsamer HP-Verlust
- 🔥 **Lava-Höhlen** – sofortiger Tod
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
├── world.py        # Prozedurale Welt-Generierung
├── player.py       # Spieler-Logik
├── tile.py         # Tile-Typen
├── camera.py       # Kamera
├── ui.py           # HUD + Screens
├── highscore.py    # Lokale Bestenliste
├── constants.py    # Alle Konstanten
└── tests/          # Pytest Tests
```

Game build with my kids

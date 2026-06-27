# 🪨 Excavate Game

Ein 2D Side-View Graber-Spiel – entwickelt von **TEC** (T, E & C) mit Python + Pygame.
Grab dich durch unendliche Schichten, sammle Ressourcen und finde den riesigen Diamanten!

## 🌐 Direkt im Browser spielen

**👉 [chriskujawa.github.io/excavate-game](https://chriskujawa.github.io/excavate-game/)**

Keine Installation nötig – läuft direkt im Browser dank [Pygbag](https://pygame-web.github.io/) (WebAssembly).

---

## 💻 Lokal spielen

```bash
pip install pygame-ce
python main.py
```

## 🧪 Tests ausführen

```bash
pip install pytest
python -m pytest tests/ -v
```

---

## 🎮 Steuerung

| Taste | Aktion |
|-------|--------|
| `← →` | Bewegen (gegen Wand = automatisch graben) |
| `↑` / `SPACE` | Springen |
| `↓` / `S` | Nach unten graben |
| `Q` | Links graben |
| `E` | Rechts graben |
| `R` | Neustart |
| `ESC` | Beenden |

---

## 🌍 Die Welt

Die Welt ist **unendlich** – in alle Richtungen. Neue Bereiche werden on-the-fly generiert.
Gleicher Seed = immer gleiche Welt.

### Tiefen-Zonen

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
| 🌑 | 190+ | Urkern (∞) | Lv 9 |

### Gefahren

- 💧 **Wasser-Höhlen** – HP sinkt langsam. Wasser fließt nach unten!
- 🔥 **Lava-Höhlen** – sofortiger Tod. Lava fließt nach unten!
- Je tiefer, desto mehr Lava (5% an der Oberfläche → 80% in großer Tiefe)

---

## 💎 Ressourcen & Punkte

| Ressource | Punkte | Wo zu finden |
|-----------|--------|--------------|
| 🖤 Kohle | 5 | Oberfläche |
| 🟤 Eisen | 15 | Bruchstein / Fester Stein |
| 💚 Smaragd | 40 | Fester Stein / Granit |
| ❤️ Rubin | 80 | Granit / Obsidian |
| 💙 Saphir | 100 | Obsidian / Basalt |
| 🟡 Gold | 150 | Obsidian / Basalt |
| 🩶 Platin | 250 | Basalt / Quarz |
| 🩷 Opal | 400 | Quarz / Tiefer Kristall |
| 💜 Amethyst | 600 | Tiefer Kristall / Urkern |
| 🦴 **Fossil** | **1000** | **Quarz bis Urkern (sehr selten!)** |
| 💎 Riesdiamant | **WIN** | Tiefe 195, x=0 |

## ⛏ Pickaxe-Upgrades

| Punkte | Level | Kann abbauen |
|--------|-------|--------------|
| 50 | Lv 2 | Bruchstein |
| 150 | Lv 3 | Fester Stein |
| 350 | Lv 4 | Granit |
| 700 | Lv 5 | Obsidian |
| 1200 | Lv 6 | Basalt |
| 2000 | Lv 7 | Quarz |
| 3000 | Lv 8 | Tiefer Kristall |
| 5000 | Lv 9 | Urkern |

---

## 🏆 Highscore

- Top-5 Bestenliste wird lokal gespeichert
- Erscheint bei Tod **und** beim Diamant-Finden
- Beim Tod mit neuem Highscore → Namenseingabe

---

## 🏗️ Projektstruktur

```
excavate-game/
├── main.py         # Einstiegspunkt (pygbag-kompatibel, async)
├── game.py         # Spielschleife + Zustände
├── world.py        # Prozedurale & unendlich expandierbare Welt
├── player.py       # TEC – Spieler-Logik
├── tile.py         # Tile-Typen
├── camera.py       # Kamera (vertikal + horizontal, unendlich)
├── ui.py           # HUD, Start/Game-Over/Win-Screens
├── highscore.py    # Lokale Bestenliste (Top 5)
├── constants.py    # Alle Konstanten
├── tests/          # Pytest-Tests
└── .github/
    └── workflows/
        └── deploy-pages.yml  # Auto-Deploy auf GitHub Pages
```

---

> Made with ❤️ by **T**, **E** & **C**



Game build with my kids

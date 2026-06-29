# agents.md — Excavate Game

This file is for AI agents (and contributors) working on this project.
It captures architecture decisions, caveats, and what was learned while building the game.

---

## Project at a Glance

**Excavate Game** is a 2D side-view pixel mining game built with Python + Pygame.
Built by T, E & C (a family project, vibe-coded with GitHub Copilot).

- **Play online:** https://chriskujawa.github.io/excavate-game/
- **Runtime:** Python 3.12+, `pygame-ce`
- **Web:** [Pygbag](https://pygame-web.github.io/) (compiles to WebAssembly / runs in browser)
- **Tests:** pytest (222 tests)

---

## How to Run

```bash
# Install dependencies
pip install -r requirements.txt   # pygame + pytest

# Run locally
python main.py

# Run tests (must be run from repo root)
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy pytest tests/ -v

# Build for web (GitHub Actions does this automatically on push to main)
pip install pygame-ce pygbag
pygbag --build main.py
# Output: build/web/
```

---

## Project Structure

```
excavate-game/
├── main.py            # Entry point — async main loop (required for pygbag)
├── game.py            # Game loop, state machine, input handling
├── world.py           # Procedural world — tile grid, generation, fluid simulation
├── player.py          # Player logic — movement, digging, collision, upgrades
├── camera.py          # Camera — follows player, converts world↔screen coords
├── tile.py            # Tile types (AIR, GROUND, RESOURCE, DIAMOND, WATER, LAVA, ACID, BEDROCK)
├── ui.py              # All rendering — HUD, screens, dwarf character, QR
├── worm.py            # Two worm enemy types: TrailWorm + CaveWorm
├── touch_controls.py  # On-screen touch buttons (shown only on web/emscripten)
├── highscore.py       # Top-5 local leaderboard (JSON file)
├── constants.py       # All game constants — single source of truth
├── highscores.json    # Persisted highscore data (gitignored in prod, committed here)
├── pyproject.toml     # pytest config (pythonpath = ["."])
├── requirements.txt   # pip dependencies: pygame, pytest
├── tests/             # Pytest test suite — 222 tests across 7 files
└── .github/
    ├── workflows/ci.yml             # Run tests on every push/PR
    └── workflows/deploy-pages.yml  # Build with pygbag + deploy to GitHub Pages
```

---

## Architecture

### State Machine (`game.py`)

The `Game` class drives a simple state machine:

```
START → PLAYING → LEVEL_COMPLETE → PLAYING (next level)
                ↘ NAME_INPUT → GAME_OVER / WIN
                ↘ GAME_OVER
                ↘ WIN
```

States: `START`, `PLAYING`, `LEVEL_COMPLETE`, `GAME_OVER`, `WIN`, `NAME_INPUT`

### Async Main Loop

`main.py` uses `asyncio` — **required** for pygbag (WebAssembly). The game loop calls
`await asyncio.sleep(0)` every frame to yield to the browser event loop.
Do **not** remove the `async`/`await` pattern.

### World (`world.py`)

- Tiles stored as `dict[(tx, ty), Tile]` — sparse, generates on demand
- **World wraps horizontally**: fixed width `WORLD_WRAP_WIDTH = 60` tiles, player re-enters from the other side
- World expands **vertically** downward as the player digs deeper (`ensure_depth`)
- Each tile coordinate is looked up with `tx % WORLD_WRAP_WIDTH` — always use `world.get(tx, ty)` not direct dict access
- Procedural generation uses per-tile deterministic RNG (`_tile_rng`) so regions can be generated in any order
- Fluids (water, lava, acid) simulate every 6 frames via `tick_fluids()`
- CaveWorms (`worm.py`) are embedded in the world and move through air tiles

### Camera (`camera.py`)

- Tracks `offset_x`, `offset_y` with lag (`CAMERA_LAG = 0.1`)
- **Reads screen size dynamically** from `pygame.display.get_surface()` — never uses `C.SCREEN_WIDTH/HEIGHT` constants
- This is intentional: supports fullscreen toggle (F11) at any resolution without restart
- `world_to_screen_x/y()` and `apply(rect)` convert world coords to screen coords
- `visible_tile_range()` / `visible_col_range()` return only tiles that need drawing

### Rendering (`ui.py`, `game.py`)

- All UI methods receive `surface` and use `surface.get_width()/get_height()` — never hardcoded resolution
- `UI.draw_dwarf(surface, rect, facing, scale)` — static method, draws the player character as a layered dwarf sprite with pickaxe; facing flips the pickaxe direction
- Player facing (`"left"` / `"right"`) is tracked in `Player.facing`, updated on horizontal movement
- The start-screen character uses `draw_dwarf(scale=2)` — same function, just scaled up

### Touch Controls (`touch_controls.py`)

- Only visible when running under emscripten (web/pygbag): `import sys; sys.platform == "emscripten"`
- Buttons at the bottom of the screen; supports multi-touch
- `HELD` actions (left/right) fire every frame while pressed; `ONESHOT` actions (jump, dig) fire once per press
- Touch state is merged into the keyboard state in `game.py` via `InputState`

### Level System

- 5 levels (`MAX_LEVELS = 5`), each with increasing diamond depth and world size
- Diamond depths per level: `[50, 105, 160, 185, 195]` tiles
- TrailWorm (follows player's dig trail) activates from Level 2 onward
- CaveWorms (roam caves) appear from world generation
- Level complete screen shown between levels; player score carries over

---

## Key Constraints & Gotchas

### pygbag / Web Build
- `main.py` **must** use `async def main()` + `asyncio.run()` — pygbag wraps this for WASM
- `pygame.display.set_mode()` in the web build: use `(0, 0)` for fullscreen or `(W, H)` for windowed — but do **not** pass `pygame.RESIZABLE` (breaks pygbag)
- The green flash on load (`#00ff00`) is pygbag's default canvas color. Fixed by filling and flipping immediately after `set_mode()` in `main.py`
- CSS on the loading page: **do not** set `display:flex` or `position` on `body` — pygbag uses `position:absolute` canvas. **Do not** add `border` or `padding` to `canvas` — breaks mouse coordinate mapping
- Fullscreen uses `pygame.SCALED` flag for correct coordinate mapping on all platforms

### Camera / Resolution
- Camera always reads live screen dimensions — changes take effect immediately after fullscreen toggle
- `C.SCREEN_WIDTH` / `C.SCREEN_HEIGHT` are only used as the **initial** windowed size in `main.py`
- Never use those constants in camera or UI drawing code — use `surface.get_width()/get_height()` instead

### World Coordinates
- World tiles use `(tx, ty)` where `tx` wraps modulo `WORLD_WRAP_WIDTH`
- Always access tiles via `world.get(tx, ty)` — never index `_tiles` directly
- Pixel position = `tx * TILE_SIZE`, `ty * TILE_SIZE`
- Player's `depth()` = `max(0, rect.top // TILE_SIZE - 2)` (2-tile surface offset)

### Tests
- Must run from repo root (pyproject.toml sets `pythonpath = ["."]`)
- Require SDL dummy drivers: `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`
- `tests/conftest.py` sets those env vars automatically for pytest runs
- Tests cover: world generation, player physics, camera, tile types, worm behavior, touch controls, highscore, game states

---

## CI / CD

### CI (`ci.yml`)
- Runs on **every push and PR** to any branch
- Python 3.14, installs `requirements.txt`, runs `pytest tests/ -v`
- SDL dummy drivers set via env vars in the workflow

### Deploy (`deploy-pages.yml`)
- Triggers on push to **`main`** only
- Uses Python 3.12 (pygbag is more stable on 3.12 than 3.14)
- Builds with `pygbag --build main.py` → output in `build/web/`
- Post-processes `build/web/index.html` to inject dark/gold loading screen theme
- Deploys to GitHub Pages via `actions/deploy-pages`

---

## What We Learned / Design Decisions

| Decision | Reason |
|----------|--------|
| Sparse `dict` for tiles | World is infinite — array would waste memory; dict generates on demand |
| Horizontal world wrap (not infinite) | Simpler generation + worm AI; 60-tile width feels natural |
| Camera reads live screen size | Supports F11 fullscreen without restarting or rescaling |
| `async` main loop | Required by pygbag for WASM; `await asyncio.sleep(0)` yields to browser |
| `pygame-ce` instead of `pygame` | Community Edition has better web/WASM support via pygbag |
| Dwarf drawn purely with `pygame.draw.*` | No external assets needed; scales with `scale` param; facing flips pickaxe |
| `pyproject.toml` sets `pythonpath` | Allows `pytest tests/` from repo root without `PYTHONPATH` hacks |
| Fill canvas black before `Game()` | Prevents green flash (`#00ff00`) from pygbag's default canvas color |
| English for all in-game text | Broader reach; avoids encoding issues in pygbag WebAssembly builds |

---

## Extending the Game

### Adding a new tile type
1. Add variant to `TileKind` enum in `tile.py`
2. Add `make_<type>()` factory function in `tile.py`
3. Update `_collides_with_solid()` in `player.py` if it should be solid
4. Update `_generate_cols()` in `world.py` to place it
5. Update `tick_fluids()` if it should flow
6. Add rendering color — tile carries its own `color` field

### Adding a new zone / depth layer
- Edit the `ZONES` list in `constants.py`
- Each zone needs: `name`, `from`, `to`, `hardness`, `color`
- `get_zone_index(depth)` in `tile.py` will pick it up automatically

### Adding a new level
- Increment `MAX_LEVELS` in `constants.py`
- Add entries to `LEVEL_DIAMOND_DEPTHS` and `LEVEL_WORLD_DEPTHS`

### Adding tests
- Tests live in `tests/`, must be named `test_*.py`
- Use `conftest.py` fixtures for pygame init — don't init pygame manually in tests
- Run: `pytest tests/ -v` from repo root

---

## Testing Convention

**Every new feature and every bug fix must include tests.**

- New feature → add tests that verify the expected behaviour
- Bug fix → add a test that would have caught the bug (regression test)
- Tests must pass before committing: `pytest tests/ -v`
- Do not reduce or remove existing tests — if a refactor breaks a test, fix the code, not the test

This keeps the test suite meaningful and prevents regressions as the game grows.

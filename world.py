import random
import constants as C
from tile import (
    Tile, TileKind,
    make_air, make_ground, make_resource, make_water, make_lava, make_acid,
    make_diamond, get_zone_index,
)
from worm import CaveWorm


def diamond_depth_for_level(level: int) -> int:
    """Gibt die Diamant-Tiefe (in Tiles) für das angegebene Level zurück."""
    idx = min(level - 1, len(C.LEVEL_DIAMOND_DEPTHS) - 1)
    return C.LEVEL_DIAMOND_DEPTHS[idx]


def world_depth_for_level(level: int) -> int:
    """Gibt die initiale Welt-Starttiefe für das angegebene Level zurück."""
    idx = min(level - 1, len(C.LEVEL_WORLD_DEPTHS) - 1)
    return C.LEVEL_WORLD_DEPTHS[idx]


class World:
    def __init__(self, seed: int = None, level: int = 1):
        self.seed = seed if seed is not None else random.randint(0, 999999)
        self.level = level
        self._tiles: dict[tuple[int, int], Tile] = {}
        # World wraps horizontally: columns [0, WORLD_WRAP_WIDTH)
        self.min_tx: int = 0
        self.max_tx: int = C.WORLD_WRAP_WIDTH
        self.max_ty: int = 0   # exclusive: rows [0, max_ty)
        self.cave_worms: list[CaveWorm] = []

        initial_depth = world_depth_for_level(level)
        self._generate_cols(0, C.WORLD_WRAP_WIDTH, 0, initial_depth)
        self._place_diamond(C.WORLD_WRAP_WIDTH // 2, diamond_depth_for_level(level))

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    @property
    def width(self) -> int:
        return C.WORLD_WRAP_WIDTH

    def surface_y(self) -> int:
        return 2

    def get(self, tx: int, ty: int) -> Tile:
        if ty < 0:
            return make_air()
        return self._tiles.get((tx % C.WORLD_WRAP_WIDTH, ty), make_air())

    def set(self, tx: int, ty: int, tile: Tile):
        if ty >= 0:
            self._tiles[(tx % C.WORLD_WRAP_WIDTH, ty)] = tile

    def remove(self, tx: int, ty: int):
        self.set(tx, ty, make_air())

    def ensure_depth(self, ty: int, padding: int = 20):
        """Generate new rows downward if player digs close to the current bottom."""
        if ty + padding >= self.max_ty:
            new_max_ty = ty + padding + C.WORLD_EXPAND_DEPTH
            self._generate_cols(0, C.WORLD_WRAP_WIDTH, self.max_ty, new_max_ty)

    def tick_fluids(self):
        fluid_kinds = (TileKind.WATER, TileKind.LAVA, TileKind.ACID)
        wrap = C.WORLD_WRAP_WIDTH

        # Downward flow – bottom-up so moved tiles aren't re-processed
        for ty in range(self.max_ty - 2, self.surface_y() - 1, -1):
            for tx in range(wrap):
                tile = self._tiles.get((tx, ty))
                if tile is None or tile.kind not in fluid_kinds:
                    continue
                below = self._tiles.get((tx, ty + 1))
                if below is not None and below.kind == TileKind.AIR:
                    self._tiles[(tx, ty + 1)] = tile
                    self._tiles[(tx, ty)] = make_air()

        # Sideways flow – only spread when sitting on solid ground
        for ty in range(self.surface_y(), self.max_ty - 1):
            for tx in range(wrap):
                tile = self._tiles.get((tx, ty))
                if tile is None or tile.kind not in fluid_kinds:
                    continue
                below = self._tiles.get((tx, ty + 1))
                if below is None or below.kind == TileKind.AIR:
                    continue  # Will fall next tick; skip sideways spread
                for d in (1, -1):
                    ntx = (tx + d) % wrap
                    neighbor = self._tiles.get((ntx, ty))
                    if neighbor is None or neighbor.kind == TileKind.AIR:
                        self._tiles[(ntx, ty)] = tile
                        break

    # ------------------------------------------------------------------ #
    #  Generation                                                          #
    # ------------------------------------------------------------------ #

    def _tile_rng(self, tx: int, ty: int) -> random.Random:
        """Independent per-tile RNG – enables generating any region in any order."""
        combined = (self.seed * 2246822519 + tx * 2654435761 + ty * 6364136219) & 0xFFFFFFFF
        return random.Random(combined)

    def _make_tile(self, tx: int, ty: int) -> Tile:
        if ty < self.surface_y():
            return make_air()
        zi = get_zone_index(ty)
        rng = self._tile_rng(tx, ty)
        for res_name, res in C.RESOURCES.items():
            prob = res["prob"][zi]
            if prob > 0 and rng.random() < prob:
                return make_resource(res_name, zi)
        return make_ground(zi)

    def _generate_cols(self, from_tx: int, to_tx: int, from_ty: int, to_ty: int):
        """Generate tiles for columns [from_tx, to_tx) and rows [from_ty, to_ty)."""
        for tx in range(from_tx, to_tx):
            for ty in range(from_ty, to_ty):
                if (tx, ty) not in self._tiles:
                    self._tiles[(tx, ty)] = self._make_tile(tx, ty)
        self._generate_caves_for(from_tx, to_tx, from_ty, to_ty)
        self.max_ty = max(self.max_ty, to_ty)

    def _cave_weights(self, cy: int) -> list[float]:
        """Fluid weights change linearly with depth.
        Reihenfolge: [empty, lava, water, acid]
        Tiefe 0   → [70, 10, 15, 5]  (viel Luft, wenig Lava, etwas Wasser)
        Tiefe 200 → [10, 55, 5,  30] (fast nur Lava und Säure)
        """
        t = min(1.0, cy / 200.0)
        empty = 70 - 60 * t
        lava  = 10 + 45 * t
        water = 15 - 10 * t
        acid  =  5 + 25 * t
        return [empty, lava, water, acid]

    def _generate_caves_for(self, from_tx: int, to_tx: int, from_ty: int, to_ty: int):
        """Carve organic blob-shaped caves using a random walk."""
        region_w = to_tx - from_tx
        region_h = to_ty - from_ty
        if region_w <= 0 or region_h <= 0:
            return
        total_tiles = region_w * region_h
        num_caves = max(1, round(total_tiles * C.CAVE_COUNT /
                                 (C.WORLD_WRAP_WIDTH * C.WORLD_INITIAL_DEPTH)))
        rng = random.Random((self.seed ^ (from_tx * 777 + to_tx * 333 +
                                          from_ty * 11 + to_ty * 19)) & 0xFFFFFFFF)
        for _ in range(num_caves):
            cx = rng.randint(from_tx, to_tx - 1)
            cy = rng.randint(max(from_ty, self.surface_y() + 3), to_ty - 3)
            size = rng.randint(C.CAVE_MIN_SIZE, C.CAVE_MAX_SIZE)
            cave_type = rng.choices(["empty", "lava", "water", "acid"],
                                    weights=self._cave_weights(cy))[0]

            # Random-walk blob: visit `size * 4` steps from the center
            wx, wy = cx, cy
            steps = size * 4
            visited: set[tuple[int, int]] = set()
            for _ in range(steps):
                visited.add((wx, wy))
                dx, dy = rng.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
                wx = from_tx + (wx - from_tx + dx) % region_w
                wy = max(self.surface_y(), min(to_ty - 1, wy + dy))

            def _fill(t, nx, ny):
                if cave_type == "empty" or t == "roof":
                    self._tiles[(nx, ny)] = make_air()
                elif cave_type == "lava":
                    self._tiles[(nx, ny)] = make_lava()
                elif cave_type == "water":
                    self._tiles[(nx, ny)] = make_water()
                else:
                    self._tiles[(nx, ny)] = make_acid()

            # Carve visited tiles; always leave top row as air (looks better)
            min_vy = min(p[1] for p in visited) if visited else cy
            for (vx, vy) in visited:
                if vy >= self.surface_y():
                    tag = "roof" if vy == min_vy else "body"
                    _fill(tag, vx % C.WORLD_WRAP_WIDTH, vy)

            # In leeren Höhlen lauert ein Höhlenwurm
            if cave_type == "empty" and visited:
                center_x = (cx % C.WORLD_WRAP_WIDTH)
                self.cave_worms.append(CaveWorm(center_x, cy))

    def _place_diamond(self, cx: int, cy: int):
        """Place a 3×3 diamond cluster at (cx, cy)."""
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = cx + dx, cy + dy
                if ny >= self.surface_y():
                    self._tiles[(nx, ny)] = make_diamond()

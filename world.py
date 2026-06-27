import random
import constants as C
from tile import (
    Tile, TileKind,
    make_air, make_ground, make_resource, make_water, make_lava,
    make_diamond, make_bedrock, get_zone_index,
)


class World:
    def __init__(self, seed: int = None):
        self.seed = seed if seed is not None else random.randint(0, 999999)
        self.height = C.WORLD_HEIGHT
        self._tiles: dict[tuple[int, int], Tile] = {}
        self.min_tx: int = 0
        self.max_tx: int = 0   # exclusive: columns are [min_tx, max_tx)

        # Generate initial columns centred around x=0
        half = C.WORLD_INITIAL_WIDTH // 2
        self._generate_cols(-half, half)
        self._place_diamond(0, self.height - 5)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #

    @property
    def width(self) -> int:
        return self.max_tx - self.min_tx

    def surface_y(self) -> int:
        return 2

    def get(self, tx: int, ty: int) -> Tile:
        if ty < 0 or ty >= self.height:
            return make_air()
        return self._tiles.get((tx, ty), make_air())

    def set(self, tx: int, ty: int, tile: Tile):
        if 0 <= ty < self.height:
            self._tiles[(tx, ty)] = tile

    def remove(self, tx: int, ty: int):
        self.set(tx, ty, make_air())

    def ensure_around(self, tx: int, padding: int = C.WORLD_EXPAND_THRESHOLD):
        """Expand world left/right if player is within padding tiles of the edge."""
        if tx - padding < self.min_tx:
            new_from = self.min_tx - C.WORLD_EXPAND_AMOUNT
            self._generate_cols(new_from, self.min_tx)
        if tx + padding >= self.max_tx:
            new_to = self.max_tx + C.WORLD_EXPAND_AMOUNT
            self._generate_cols(self.max_tx, new_to)

    def tick_fluids(self):
        fluid_kinds = (TileKind.WATER, TileKind.LAVA)
        for ty in range(self.height - 2, self.surface_y() - 1, -1):
            for tx in range(self.min_tx, self.max_tx):
                tile = self._tiles.get((tx, ty))
                if tile is None or tile.kind not in fluid_kinds:
                    continue
                below = self._tiles.get((tx, ty + 1))
                if below is not None and below.kind == TileKind.AIR:
                    self._tiles[(tx, ty + 1)] = tile
                    self._tiles[(tx, ty)] = make_air()

    # ------------------------------------------------------------------ #
    #  Generation                                                          #
    # ------------------------------------------------------------------ #

    def _col_rng(self, tx: int) -> random.Random:
        """Deterministic RNG per column (independent of generation order)."""
        return random.Random((self.seed ^ (tx * 2654435761)) & 0xFFFFFFFF)

    def _make_tile(self, tx: int, ty: int, rng: random.Random) -> Tile:
        if ty < self.surface_y():
            return make_air()
        if ty >= self.height - 2:
            return make_bedrock()
        zi = get_zone_index(ty)
        for res_name, res in C.RESOURCES.items():
            prob = res["prob"][zi]
            if prob > 0 and rng.random() < prob:
                return make_resource(res_name, zi)
        return make_ground(zi)

    def _generate_cols(self, from_tx: int, to_tx: int):
        """Generate columns [from_tx, to_tx) and update bounds."""
        for tx in range(from_tx, to_tx):
            rng = self._col_rng(tx)
            for ty in range(self.height):
                self._tiles[(tx, ty)] = self._make_tile(tx, ty, rng)
        self._generate_caves_for(from_tx, to_tx)
        self.min_tx = min(self.min_tx, from_tx)
        self.max_tx = max(self.max_tx, to_tx)

    def _generate_caves_for(self, from_tx: int, to_tx: int):
        region_width = to_tx - from_tx
        num_caves = max(1, round(region_width * C.CAVE_COUNT / C.WORLD_INITIAL_WIDTH))
        rng = random.Random((self.seed ^ (from_tx * 777 + to_tx * 333)) & 0xFFFFFFFF)
        for _ in range(num_caves):
            cx = rng.randint(from_tx, to_tx - 1)
            cy = rng.randint(5, self.height - 10)
            w  = rng.randint(C.CAVE_MIN_SIZE, C.CAVE_MAX_SIZE)
            h  = rng.randint(C.CAVE_MIN_SIZE, max(C.CAVE_MIN_SIZE, C.CAVE_MAX_SIZE // 2))
            cave_type = rng.choices(["empty", "water", "lava"], weights=[60, 25, 15])[0]
            for dy in range(h):
                for dx in range(w):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= ny < self.height - 2:
                        if cave_type == "empty":
                            self._tiles[(nx, ny)] = make_air()
                        elif cave_type == "water":
                            self._tiles[(nx, ny)] = make_water()
                        else:
                            self._tiles[(nx, ny)] = make_lava()

    def _place_diamond(self, cx: int, cy: int):
        """Place a 3×3 diamond cluster at (cx, cy)."""
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = cx + dx, cy + dy
                if 0 <= ny < self.height - 2:
                    self._tiles[(nx, ny)] = make_diamond()


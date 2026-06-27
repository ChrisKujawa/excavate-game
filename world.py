import random
import constants as C
from tile import (
    Tile, TileKind,
    make_air, make_ground, make_resource, make_water, make_lava,
    make_diamond, make_bedrock, get_zone_index,
)


class World:
    def __init__(self, seed: int = None):
        self.width = C.WORLD_WIDTH
        self.height = C.WORLD_HEIGHT
        self.rng = random.Random(seed)
        self.grid: list[list[Tile]] = []
        self._generate()

    # ------------------------------------------------------------------ #
    #  Öffentliche Methoden                                                #
    # ------------------------------------------------------------------ #

    def get(self, tx: int, ty: int) -> Tile:
        if 0 <= tx < self.width and 0 <= ty < self.height:
            return self.grid[ty][tx]
        return make_air()

    def set(self, tx: int, ty: int, tile: Tile):
        if 0 <= tx < self.width and 0 <= ty < self.height:
            self.grid[ty][tx] = tile

    def remove(self, tx: int, ty: int):
        """Tile abbauen → wird zu Luft."""
        self.set(tx, ty, make_air())

    def tick_fluids(self):
        """Lässt Wasser und Lava nach unten fließen (von unten nach oben scannen)."""
        fluid_kinds = (TileKind.WATER, TileKind.LAVA)
        # Von unten nach oben damit Fluid in einem Tick mehrere Felder fällt
        for ty in range(self.height - 2, self.surface_y() - 1, -1):
            for tx in range(self.width):
                tile = self.grid[ty][tx]
                if tile.kind not in fluid_kinds:
                    continue
                below = self.grid[ty + 1][tx]
                if below.kind == TileKind.AIR:
                    self.grid[ty + 1][tx] = tile
                    self.grid[ty][tx] = make_air()

    def surface_y(self) -> int:
        """Y-Position der Oberfläche in Tiles."""
        return 2  # erste 2 Reihen sind Luft/Himmel

    # ------------------------------------------------------------------ #
    #  Generierung                                                         #
    # ------------------------------------------------------------------ #

    def _generate(self):
        # 1) Grundgerüst: Alle Tiles nach Zone füllen
        self.grid = []
        for ty in range(self.height):
            row = []
            for tx in range(self.width):
                if ty < self.surface_y():
                    row.append(make_air())
                elif ty >= self.height - 2:
                    row.append(make_bedrock())   # unzerstörbarer Boden
                else:
                    zi = get_zone_index(ty)
                    tile = self._maybe_resource(tx, ty, zi)
                    row.append(tile)
            self.grid.append(row)

        # 2) Riesigen Diamant am Boden platzieren (Mitte)
        diamond_x = self.width // 2
        diamond_y = self.height - 5   # 2 Reihen Abstand zum Bedrock
        self.grid[diamond_y][diamond_x] = make_diamond()
        # Diamant ist 3x3 groß damit man ihn gut sieht
        for dy in range(-1, 2):
            for dx in range(-1, 2):
                nx, ny = diamond_x + dx, diamond_y + dy
                if 0 <= nx < self.width and 0 <= ny < self.height - 2:
                    if not (dx == 0 and dy == 0):
                        self.grid[ny][nx] = make_diamond()

        # 3) Höhlen einstreuen
        self._generate_caves()

    def _maybe_resource(self, tx: int, ty: int, zone_index: int) -> Tile:
        """Gibt entweder eine Ressource oder normalen Untergrund zurück."""
        for res_name, res in C.RESOURCES.items():
            prob = res["prob"][zone_index]
            if prob > 0 and self.rng.random() < prob:
                return make_resource(res_name, zone_index)
        return make_ground(zone_index)

    def _generate_caves(self):
        for _ in range(C.CAVE_COUNT):
            # Höhlen nur ab Tiefe 5 damit man nicht sofort reinfällt
            cx = self.rng.randint(2, self.width - 3)
            cy = self.rng.randint(5, self.height - 10)
            w  = self.rng.randint(C.CAVE_MIN_SIZE, C.CAVE_MAX_SIZE)
            h  = self.rng.randint(C.CAVE_MIN_SIZE, max(C.CAVE_MIN_SIZE, C.CAVE_MAX_SIZE // 2))

            cave_type = self.rng.choices(
                ["empty", "water", "lava"],
                weights=[60, 25, 15],
            )[0]

            for dy in range(h):
                for dx in range(w):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if cave_type == "empty":
                            self.grid[ny][nx] = make_air()
                        elif cave_type == "water":
                            self.grid[ny][nx] = make_water()
                        else:
                            self.grid[ny][nx] = make_lava()

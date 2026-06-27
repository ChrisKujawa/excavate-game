"""Tests für world.py – Welt-Generierung."""
import pytest
from world import World
from tile import TileKind, make_water, make_lava, make_ground
import constants as C


@pytest.fixture
def world():
    return World(seed=42)


class TestWorldDimensions:
    def test_correct_width(self, world):
        assert world.width == C.WORLD_WIDTH

    def test_correct_height(self, world):
        assert world.height == C.WORLD_HEIGHT

    def test_grid_rows(self, world):
        assert len(world.grid) == C.WORLD_HEIGHT

    def test_grid_columns(self, world):
        for row in world.grid:
            assert len(row) == C.WORLD_WIDTH


class TestWorldSurface:
    def test_surface_rows_are_air(self, world):
        for tx in range(world.width):
            for ty in range(world.surface_y()):
                assert world.get(tx, ty).kind == TileKind.AIR

    def test_below_surface_not_all_air(self, world):
        solid_count = sum(
            1 for tx in range(world.width)
            if world.get(tx, world.surface_y()).kind != TileKind.AIR
        )
        assert solid_count > 0


class TestWorldDiamond:
    def test_diamond_exists_at_bottom(self, world):
        diamond_x = world.width // 2
        diamond_y = world.height - 5
        assert world.get(diamond_x, diamond_y).kind == TileKind.DIAMOND

    def test_diamond_cluster(self, world):
        """Diamant sollte als 3x3 Block platziert sein."""
        diamond_x = world.width // 2
        diamond_y = world.height - 5
        count = sum(
            1 for dy in range(-1, 2)
            for dx in range(-1, 2)
            if world.get(diamond_x + dx, diamond_y + dy).kind == TileKind.DIAMOND
        )
        assert count == 9


class TestWorldBounds:
    def test_get_out_of_bounds_returns_air(self, world):
        assert world.get(-1, 0).kind == TileKind.AIR
        assert world.get(0, -1).kind == TileKind.AIR
        assert world.get(9999, 0).kind == TileKind.AIR

    def test_set_out_of_bounds_does_not_crash(self, world):
        from tile import make_air
        world.set(-1, 0, make_air())   # should not raise

    def test_bottom_rows_are_bedrock(self, world):
        """Die untersten 2 Reihen müssen unzerstörbares Bedrock sein."""
        for tx in range(world.width):
            assert world.get(tx, world.height - 1).kind == TileKind.BEDROCK
            assert world.get(tx, world.height - 2).kind == TileKind.BEDROCK

    def test_bedrock_cannot_be_dug(self, world):
        """Bedrock hat hardness 99 – weit über Pickaxe-Maximum."""
        tile = world.get(0, world.height - 1)
        assert tile.hardness > 5


class TestWorldRemove:
    def test_remove_replaces_with_air(self, world):
        # Finde eine solide Tile unter der Oberfläche
        tx, ty = 0, world.surface_y()
        world.set(tx, ty, __import__('tile').make_ground(0))
        world.remove(tx, ty)
        assert world.get(tx, ty).kind == TileKind.AIR


class TestWorldResources:
    def test_resources_exist_in_world(self, world):
        """Mit Seed 42 sollten irgendwo Ressourcen liegen."""
        found = any(
            world.get(tx, ty).kind == TileKind.RESOURCE
            for ty in range(world.height)
            for tx in range(world.width)
        )
        assert found

    def test_resources_not_above_surface(self, world):
        for ty in range(world.surface_y()):
            for tx in range(world.width):
                assert world.get(tx, ty).kind != TileKind.RESOURCE


class TestWorldDeterminism:
    def test_same_seed_same_world(self):
        w1 = World(seed=123)
        w2 = World(seed=123)
        for ty in range(w1.height):
            for tx in range(w1.width):
                assert w1.get(tx, ty).kind == w2.get(tx, ty).kind

    def test_different_seed_different_world(self):
        w1 = World(seed=1)
        w2 = World(seed=2)
        differences = sum(
            1 for ty in range(w1.height)
            for tx in range(w1.width)
            if w1.get(tx, ty).kind != w2.get(tx, ty).kind
        )
        assert differences > 0


class TestWorldCaves:
    def test_some_air_underground(self, world):
        """Höhlen sollten Luft unter der Oberfläche erzeugen."""
        air_underground = sum(
            1 for ty in range(world.surface_y() + 5, world.height - 5)
            for tx in range(world.width)
            if world.get(tx, ty).kind == TileKind.AIR
        )
        assert air_underground > 0


class TestFluidSimulation:
    def _make_fresh_world(self):
        w = World(seed=1)
        # Leere die ganze Welt unterhalb der Oberfläche für kontrollierte Tests
        from tile import make_air
        for ty in range(w.surface_y(), w.height):
            for tx in range(w.width):
                w.grid[ty][tx] = make_air()
        return w

    def test_water_falls_into_air_below(self):
        w = self._make_fresh_world()
        w.set(5, 10, make_water())   # Wasser oben
        # darunter bleibt Luft (schon gelöscht)
        w.tick_fluids()
        assert w.get(5, 11).kind == TileKind.WATER
        assert w.get(5, 10).kind == TileKind.AIR

    def test_lava_falls_into_air_below(self):
        w = self._make_fresh_world()
        w.set(5, 10, make_lava())
        w.tick_fluids()
        assert w.get(5, 11).kind == TileKind.LAVA
        assert w.get(5, 10).kind == TileKind.AIR

    def test_fluid_does_not_fall_through_solid(self):
        from tile import make_ground
        w = self._make_fresh_world()
        w.set(5, 10, make_water())
        w.set(5, 11, make_ground(0))   # solide Tile darunter
        w.tick_fluids()
        assert w.get(5, 10).kind == TileKind.WATER   # bleibt oben
        assert w.get(5, 11).kind == TileKind.GROUND  # Stein bleibt

    def test_fluid_falls_multiple_tiles(self):
        """Mehrere tick_fluids-Aufrufe lassen Fluid weiter fallen."""
        w = self._make_fresh_world()
        w.set(5, 10, make_water())
        for _ in range(5):
            w.tick_fluids()
        # Nach 5 Ticks sollte Wasser mindestens 5 Felder tiefer sein
        assert w.get(5, 10).kind == TileKind.AIR
        assert w.get(5, 15).kind == TileKind.WATER

    def test_water_stays_if_no_air_below(self):
        from tile import make_ground
        w = self._make_fresh_world()
        w.set(5, 10, make_water())
        # Fülle alles darunter mit Stein
        for ty in range(11, 20):
            w.set(5, ty, make_ground(0))
        w.tick_fluids()
        assert w.get(5, 10).kind == TileKind.WATER  # bleibt

    def test_fluid_does_not_exceed_world_bottom(self):
        w = self._make_fresh_world()
        bottom = w.height - 1
        w.set(5, bottom, make_water())
        w.tick_fluids()   # darf nicht crashen
        # Fluid bleibt am Boden (nichts darunter)
        assert w.get(5, bottom).kind == TileKind.WATER

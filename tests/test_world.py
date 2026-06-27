"""Tests für world.py – Welt-Generierung."""
import pytest
from world import World
from tile import TileKind, make_water, make_lava, make_ground, make_air
import constants as C


@pytest.fixture
def world():
    return World(seed=42)


class TestWorldDimensions:
    def test_correct_height(self, world):
        assert world.height == C.WORLD_HEIGHT

    def test_initial_width(self, world):
        assert world.width == C.WORLD_INITIAL_WIDTH

    def test_min_max_tx(self, world):
        half = C.WORLD_INITIAL_WIDTH // 2
        assert world.min_tx == -half
        assert world.max_tx == half


class TestWorldSurface:
    def test_surface_rows_are_air(self, world):
        for tx in range(world.min_tx, world.max_tx):
            for ty in range(world.surface_y()):
                assert world.get(tx, ty).kind == TileKind.AIR

    def test_below_surface_not_all_air(self, world):
        solid_count = sum(
            1 for tx in range(world.min_tx, world.max_tx)
            if world.get(tx, world.surface_y()).kind != TileKind.AIR
        )
        assert solid_count > 0


class TestWorldDiamond:
    def test_diamond_exists_at_centre(self, world):
        assert world.get(0, world.height - 5).kind == TileKind.DIAMOND

    def test_diamond_cluster(self, world):
        count = sum(
            1 for dy in range(-1, 2)
            for dx in range(-1, 2)
            if world.get(dx, world.height - 5 + dy).kind == TileKind.DIAMOND
        )
        assert count == 9


class TestWorldBounds:
    def test_get_outside_y_returns_air(self, world):
        assert world.get(0, -1).kind == TileKind.AIR
        assert world.get(0, world.height).kind == TileKind.AIR

    def test_get_ungenerated_x_returns_air(self, world):
        assert world.get(world.max_tx + 100, 5).kind == TileKind.AIR

    def test_set_out_of_bounds_does_not_crash(self, world):
        world.set(0, -1, make_air())

    def test_bottom_rows_are_bedrock(self, world):
        for tx in range(world.min_tx, world.max_tx):
            assert world.get(tx, world.height - 1).kind == TileKind.BEDROCK
            assert world.get(tx, world.height - 2).kind == TileKind.BEDROCK

    def test_bedrock_cannot_be_dug(self, world):
        tile = world.get(0, world.height - 1)
        assert tile.hardness > 5


class TestWorldExpansion:
    def test_ensure_around_expands_right(self, world):
        before = world.max_tx
        world.ensure_around(world.max_tx - 1)
        assert world.max_tx > before

    def test_ensure_around_expands_left(self, world):
        before = world.min_tx
        world.ensure_around(world.min_tx + 1)
        assert world.min_tx < before

    def test_expanded_columns_have_bedrock(self, world):
        old_max = world.max_tx
        world.ensure_around(world.max_tx - 1)
        for tx in range(old_max, world.max_tx):
            assert world.get(tx, world.height - 1).kind == TileKind.BEDROCK

    def test_no_duplicate_expansion(self, world):
        world.ensure_around(world.max_tx - 1)
        size_after_first = world.width
        world.ensure_around(0)  # near centre, no expansion needed
        assert world.width == size_after_first

    def test_expansion_is_deterministic(self):
        w1 = World(seed=77)
        w2 = World(seed=77)
        w1.ensure_around(w1.max_tx - 1)
        w2.ensure_around(w2.max_tx - 1)
        for ty in range(5, 20):
            for tx in range(w1.min_tx, w1.max_tx):
                assert w1.get(tx, ty).kind == w2.get(tx, ty).kind


class TestWorldRemove:
    def test_remove_replaces_with_air(self, world):
        world.set(0, world.surface_y(), make_ground(0))
        world.remove(0, world.surface_y())
        assert world.get(0, world.surface_y()).kind == TileKind.AIR


class TestWorldResources:
    def test_resources_exist_in_world(self, world):
        found = any(
            world.get(tx, ty).kind == TileKind.RESOURCE
            for ty in range(world.height)
            for tx in range(world.min_tx, world.max_tx)
        )
        assert found

    def test_resources_not_above_surface(self, world):
        for ty in range(world.surface_y()):
            for tx in range(world.min_tx, world.max_tx):
                assert world.get(tx, ty).kind != TileKind.RESOURCE


class TestWorldDeterminism:
    def test_same_seed_same_world(self):
        w1 = World(seed=123)
        w2 = World(seed=123)
        for ty in range(w1.height):
            for tx in range(w1.min_tx, w1.max_tx):
                assert w1.get(tx, ty).kind == w2.get(tx, ty).kind

    def test_different_seed_different_world(self):
        w1 = World(seed=1)
        w2 = World(seed=2)
        diffs = sum(
            1 for ty in range(w1.height)
            for tx in range(w1.min_tx, w1.max_tx)
            if w1.get(tx, ty).kind != w2.get(tx, ty).kind
        )
        assert diffs > 0


class TestWorldCaves:
    def test_some_air_underground(self, world):
        air_underground = sum(
            1 for ty in range(world.surface_y() + 5, world.height - 5)
            for tx in range(world.min_tx, world.max_tx)
            if world.get(tx, ty).kind == TileKind.AIR
        )
        assert air_underground > 0


class TestFluidSimulation:
    def _make_fresh_world(self):
        w = World(seed=1)
        for ty in range(w.surface_y(), w.height - 2):
            for tx in range(w.min_tx, w.max_tx):
                w.set(tx, ty, make_air())
        return w

    def test_water_falls_into_air_below(self):
        w = self._make_fresh_world()
        w.set(5, 10, make_water())
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
        w = self._make_fresh_world()
        w.set(5, 10, make_water())
        w.set(5, 11, make_ground(0))
        w.tick_fluids()
        assert w.get(5, 10).kind == TileKind.WATER
        assert w.get(5, 11).kind == TileKind.GROUND

    def test_fluid_falls_multiple_tiles(self):
        w = self._make_fresh_world()
        w.set(5, 10, make_water())
        for _ in range(5):
            w.tick_fluids()
        assert w.get(5, 10).kind == TileKind.AIR
        assert w.get(5, 15).kind == TileKind.WATER

    def test_water_stays_if_no_air_below(self):
        w = self._make_fresh_world()
        w.set(5, 10, make_water())
        for ty in range(11, 20):
            w.set(5, ty, make_ground(0))
        w.tick_fluids()
        assert w.get(5, 10).kind == TileKind.WATER

    def test_fluid_does_not_exceed_world_bottom(self):
        w = self._make_fresh_world()
        bottom = w.height - 1
        w.set(5, bottom, make_water())
        w.tick_fluids()
        assert w.get(5, bottom).kind == TileKind.WATER

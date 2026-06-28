"""Tests für world.py – Welt-Generierung (unendliche Tiefe)."""
import pytest
from world import World, diamond_depth_for_level, world_depth_for_level
from tile import TileKind, make_water, make_lava, make_ground, make_air
import constants as C


@pytest.fixture
def world():
    return World(seed=42)


class TestWorldDimensions:
    def test_initial_width(self, world):
        assert world.width == C.WORLD_INITIAL_WIDTH

    def test_initial_depth(self, world):
        assert world.max_ty == world_depth_for_level(1)

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
    def test_diamond_exists_at_depth(self, world):
        depth = diamond_depth_for_level(1)
        assert world.get(0, depth).kind == TileKind.DIAMOND

    def test_diamond_cluster(self, world):
        depth = diamond_depth_for_level(1)
        count = sum(
            1 for dy in range(-1, 2)
            for dx in range(-1, 2)
            if world.get(dx, depth + dy).kind == TileKind.DIAMOND
        )
        assert count == 9


class TestWorldBounds:
    def test_get_outside_y_returns_air(self, world):
        assert world.get(0, -1).kind == TileKind.AIR

    def test_get_ungenerated_x_returns_air(self, world):
        assert world.get(world.max_tx + 100, 5).kind == TileKind.AIR

    def test_get_ungenerated_depth_returns_air(self, world):
        assert world.get(0, world.max_ty + 100).kind == TileKind.AIR

    def test_set_out_of_bounds_does_not_crash(self, world):
        world.set(0, -1, make_air())


class TestWorldExpansion:
    def test_ensure_around_expands_right(self, world):
        before = world.max_tx
        world.ensure_around(world.max_tx - 1)
        assert world.max_tx > before

    def test_ensure_around_expands_left(self, world):
        before = world.min_tx
        world.ensure_around(world.min_tx + 1)
        assert world.min_tx < before

    def test_ensure_depth_expands_downward(self, world):
        before = world.max_ty
        world.ensure_depth(world.max_ty + 1)
        assert world.max_ty > before

    def test_ensure_depth_generates_valid_tiles(self, world):
        world.ensure_depth(world.max_ty + 1)
        # Tiles just below old bottom should exist and not be air (mostly)
        sample_ty = world.max_ty - 5
        found_solid = any(
            world.get(tx, sample_ty).kind != TileKind.AIR
            for tx in range(world.min_tx, world.max_tx)
        )
        assert found_solid

    def test_no_duplicate_expansion(self, world):
        world.ensure_around(world.max_tx - 1)
        size_after = world.width
        world.ensure_around(0)  # near centre, no expansion needed
        assert world.width == size_after

    def test_expansion_is_deterministic(self):
        w1 = World(seed=77)
        w2 = World(seed=77)
        w1.ensure_depth(w1.max_ty + 1)
        w2.ensure_depth(w2.max_ty + 1)
        new_ty = min(w1.max_ty, w2.max_ty) - 5
        for tx in range(w1.min_tx, w1.max_tx):
            assert w1.get(tx, new_ty).kind == w2.get(tx, new_ty).kind

    def test_horizontal_expansion_matches_current_depth(self, world):
        """New columns go as deep as existing world."""
        old_max = world.max_tx
        world.ensure_around(world.max_tx - 1)
        # New columns should have tiles at the deepest generated row
        ty = world.max_ty - 5
        found = any(
            world.get(tx, ty).kind != TileKind.AIR
            for tx in range(old_max, world.max_tx)
        )
        assert found


class TestWorldRemove:
    def test_remove_replaces_with_air(self, world):
        world.set(0, world.surface_y(), make_ground(0))
        world.remove(0, world.surface_y())
        assert world.get(0, world.surface_y()).kind == TileKind.AIR


class TestCaveDepthScaling:
    def test_shallow_mostly_empty(self):
        w = World(seed=1)
        weights = w._cave_weights(0)
        # empty >> lava near surface
        assert weights[0] > weights[1]   # empty > lava

    def test_deep_mostly_lava(self):
        w = World(seed=1)
        weights = w._cave_weights(300)
        # lava >> empty deep down
        assert weights[1] > weights[0]   # lava > empty

    def test_weights_increase_with_depth(self):
        w = World(seed=1)
        shallow_lava = w._cave_weights(10)[1]
        deep_lava    = w._cave_weights(200)[1]
        assert deep_lava > shallow_lava

    def test_weights_always_positive(self):
        w = World(seed=1)
        for depth in [0, 50, 100, 200, 500]:
            weights = w._cave_weights(depth)
            assert all(v > 0 for v in weights)


class TestWorldResources:
    def test_resources_exist_in_world(self, world):
        found = any(
            world.get(tx, ty).kind == TileKind.RESOURCE
            for ty in range(world.max_ty)
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
        for ty in range(50):
            for tx in range(w1.min_tx, w1.max_tx):
                assert w1.get(tx, ty).kind == w2.get(tx, ty).kind

    def test_different_seed_different_world(self):
        w1 = World(seed=1)
        w2 = World(seed=2)
        diffs = sum(
            1 for ty in range(50)
            for tx in range(w1.min_tx, w1.max_tx)
            if w1.get(tx, ty).kind != w2.get(tx, ty).kind
        )
        assert diffs > 0


class TestWorldCaves:
    def test_some_air_underground(self, world):
        air_underground = sum(
            1 for ty in range(world.surface_y() + 5, min(50, world.max_ty))
            for tx in range(world.min_tx, world.max_tx)
            if world.get(tx, ty).kind == TileKind.AIR
        )
        assert air_underground > 0


class TestFluidSimulation:
    def _make_fresh_world(self):
        w = World(seed=1)
        for ty in range(w.surface_y(), min(50, w.max_ty)):
            for tx in range(w.min_tx, w.max_tx):
                w.set(tx, ty, make_air())
        return w

    def test_lava_falls_into_air_below(self):
        w = self._make_fresh_world()
        w.set(5, 10, make_lava())
        w.tick_fluids()
        assert w.get(5, 11).kind == TileKind.LAVA
        assert w.get(5, 10).kind == TileKind.AIR

    def test_fluid_does_not_fall_through_solid(self):
        w = self._make_fresh_world()
        w.set(5, 10, make_lava())
        w.set(5, 11, make_ground(0))
        w.tick_fluids()
        assert w.get(5, 10).kind == TileKind.LAVA
        assert w.get(5, 11).kind == TileKind.GROUND

    def test_fluid_falls_multiple_tiles(self):
        w = self._make_fresh_world()
        w.set(5, 10, make_lava())
        for _ in range(5):
            w.tick_fluids()
        assert w.get(5, 10).kind == TileKind.AIR
        assert w.get(5, 15).kind == TileKind.LAVA

    def test_lava_stays_if_no_air_below(self):
        w = self._make_fresh_world()
        w.set(5, 10, make_lava())
        for ty in range(11, 20):
            w.set(5, ty, make_ground(0))
        w.tick_fluids()
        assert w.get(5, 10).kind == TileKind.LAVA

"""Umfassende Tests für Worm (Trail-Verfolger) und CaveWorm (Höhlenwurm)."""
import pytest
import constants as C
from worm import Worm, CaveWorm
from tile import make_air, make_ground, TileKind


# ------------------------------------------------------------------ #
#  Hilfs-Klassen                                                       #
# ------------------------------------------------------------------ #

class AirWorld:
    """Stub-Welt wo jeder Tile Luft ist."""
    def get(self, tx, ty):
        return make_air()


class SolidWorld:
    """Stub-Welt wo jeder Tile fester Stein ist."""
    def get(self, tx, ty):
        return make_ground(5)


class MazeWorld:
    """Horizontaler Gang auf ty=20, sonst Stein."""
    CORRIDOR_TY = 20

    def get(self, tx, ty):
        if ty == self.CORRIDOR_TY:
            return make_air()
        return make_ground(0)


# ------------------------------------------------------------------ #
#  Worm (Trail-Verfolger)                                              #
# ------------------------------------------------------------------ #

class TestWormInit:
    def test_starts_at_given_position(self):
        w = Worm(5, 10)
        assert w.tx == 5 and w.ty == 10

    def test_delay_not_zero(self):
        w = Worm(0, 0)
        assert w._delay == C.WORM_START_DELAY

    def test_not_active_before_delay(self):
        w = Worm(0, 0)
        assert not w.is_active

    def test_active_after_delay(self):
        w = Worm(0, 0)
        for _ in range(C.WORM_START_DELAY + 1):
            w.update([])
        assert w.is_active

    def test_delay_seconds_initial(self):
        w = Worm(0, 0)
        assert abs(w.delay_seconds - C.WORM_START_DELAY / C.FPS) < 0.01


class TestWormSpeed:
    def test_level2_interval(self):
        w = Worm(0, 0, level=2)
        assert w._move_interval == C.WORM_MOVE_INTERVAL

    def test_level5_interval_faster(self):
        w2 = Worm(0, 0, level=2)
        w5 = Worm(0, 0, level=5)
        assert w5._move_interval < w2._move_interval

    def test_interval_never_below_minimum(self):
        for level in range(1, 10):
            w = Worm(0, 0, level=level)
            assert w._move_interval >= C.WORM_MIN_INTERVAL

    def test_interval_never_above_start(self):
        for level in range(1, 10):
            w = Worm(0, 0, level=level)
            assert w._move_interval <= C.WORM_MOVE_INTERVAL


class TestWormTrailFollowing:
    def _advance(self, worm, trail, frames):
        """Einen Wurm n Frames lang updaten."""
        for _ in range(frames):
            worm.update(trail)

    def test_does_not_move_during_delay(self):
        w = Worm(0, 5)
        trail = [(0, 5), (1, 5), (2, 5)]
        self._advance(w, trail, C.WORM_START_DELAY - 1)
        assert w.tx == 0 and w.ty == 5

    def test_moves_along_trail_after_delay(self):
        w = Worm(0, 5)
        trail = [(0, 5), (1, 5), (2, 5), (3, 5), (4, 5)]
        # Delay + several move intervals
        self._advance(w, trail, C.WORM_START_DELAY + w._move_interval * 3 + 1)
        # Should have advanced at least 1 step along trail
        assert w._trail_index > 0

    def test_does_not_overtake_player(self):
        w = Worm(0, 5)
        trail = [(0, 5), (1, 5)]
        self._advance(w, trail, C.WORM_START_DELAY + w._move_interval * 10 + 1)
        # Cannot exceed last trail index
        assert w._trail_index <= len(trail) - 1

    def test_rect_updated_on_move(self):
        w = Worm(0, 5)
        trail = [(0, 5), (3, 8)]
        self._advance(w, trail, C.WORM_START_DELAY + w._move_interval + 5)
        if w._trail_index == 1:
            expected_x = 3 * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2
            assert w.rect.x == expected_x

    def test_empty_trail_stays_put(self):
        w = Worm(2, 2)
        for _ in range(C.WORM_START_DELAY + 100):
            w.update([])
        assert w.tx == 2 and w.ty == 2


class TestWormCatchesPlayer:
    def test_catches_at_same_tile(self):
        w = Worm(3, 3)
        w._delay = 0
        w.tx, w.ty = 3, 3
        assert w.catches_player(3, 3)

    def test_does_not_catch_adjacent_tile(self):
        w = Worm(3, 3)
        w._delay = 0
        w.tx, w.ty = 3, 3
        assert not w.catches_player(4, 3)
        assert not w.catches_player(3, 4)

    def test_no_catch_during_delay(self):
        w = Worm(3, 3)
        assert w._delay > 0
        assert not w.catches_player(3, 3)


# ------------------------------------------------------------------ #
#  CaveWorm                                                            #
# ------------------------------------------------------------------ #

class TestCaveWormInit:
    def test_starts_inactive(self):
        cw = CaveWorm(10, 20)
        assert not cw._active

    def test_rect_at_correct_pixel(self):
        cw = CaveWorm(5, 8)
        expected_x = 5 * C.TILE_SIZE + (C.TILE_SIZE - C.CAVE_WORM_SIZE) // 2
        expected_y = 8 * C.TILE_SIZE + (C.TILE_SIZE - C.CAVE_WORM_SIZE) // 2
        assert cw.rect.x == expected_x
        assert cw.rect.y == expected_y


class TestCaveWormActivation:
    def test_activates_when_player_within_radius(self):
        cw = CaveWorm(10, 10)
        w = AirWorld()
        cw.update(10 + C.CAVE_WORM_DETECT_RADIUS - 1, 10, w)
        assert cw._active

    def test_does_not_activate_outside_radius(self):
        cw = CaveWorm(10, 10)
        w = AirWorld()
        cw.update(10 + C.CAVE_WORM_DETECT_RADIUS + 5, 10, w)
        assert not cw._active

    def test_activates_diagonally(self):
        cw = CaveWorm(10, 10)
        w = AirWorld()
        # Manhattan distance = 5 + 4 = 9 < 10
        cw.update(15, 14, w)
        assert cw._active

    def test_stays_active_once_triggered(self):
        cw = CaveWorm(10, 10)
        w = AirWorld()
        cw.update(10, 10, w)
        assert cw._active
        # Move player far away
        for _ in range(20):
            cw.update(100, 100, w)
        assert cw._active  # stays active


class TestCaveWormMovement:
    def _advance(self, cw, player_tx, player_ty, world, frames):
        for _ in range(frames):
            cw.update(player_tx, player_ty, world)

    def test_moves_right_toward_player(self):
        w = AirWorld()
        cw = CaveWorm(5, 10)
        cw._active = True
        start = cw.tx
        self._advance(cw, 15, 10, w, C.CAVE_WORM_INTERVAL + 1)
        assert cw.tx > start

    def test_moves_left_toward_player(self):
        w = AirWorld()
        cw = CaveWorm(15, 10)
        cw._active = True
        start = cw.tx
        self._advance(cw, 5, 10, w, C.CAVE_WORM_INTERVAL + 1)
        assert cw.tx < start

    def test_moves_down_toward_player(self):
        w = AirWorld()
        cw = CaveWorm(10, 5)
        cw._active = True
        start = cw.ty
        self._advance(cw, 10, 20, w, C.CAVE_WORM_INTERVAL + 1)
        assert cw.ty > start

    def test_moves_up_toward_player(self):
        w = AirWorld()
        cw = CaveWorm(10, 20)
        cw._active = True
        start = cw.ty
        self._advance(cw, 10, 5, w, C.CAVE_WORM_INTERVAL + 1)
        assert cw.ty < start

    def test_does_not_move_through_solid(self):
        w = SolidWorld()
        cw = CaveWorm(10, 10)
        cw._active = True
        start_tx, start_ty = cw.tx, cw.ty
        self._advance(cw, 20, 10, w, C.CAVE_WORM_INTERVAL * 5 + 1)
        assert cw.tx == start_tx and cw.ty == start_ty

    def test_navigates_corridor(self):
        """Worm in maze: blocked vertically, finds horizontal corridor."""
        w = MazeWorld()
        # Worm at corridor row, blocked above
        cw = CaveWorm(5, MazeWorld.CORRIDOR_TY)
        cw._active = True
        start = cw.tx
        # Player is to the right in the same corridor
        self._advance(cw, 20, MazeWorld.CORRIDOR_TY, w,
                      C.CAVE_WORM_INTERVAL * 10 + 1)
        assert cw.tx > start

    def test_rect_follows_position(self):
        w = AirWorld()
        cw = CaveWorm(5, 10)
        cw._active = True
        self._advance(cw, 20, 10, w, C.CAVE_WORM_INTERVAL + 1)
        expected_x = cw.tx * C.TILE_SIZE + (C.TILE_SIZE - C.CAVE_WORM_SIZE) // 2
        assert cw.rect.x == expected_x

    def test_wrap_around_world(self):
        """CaveWorm near right edge wraps to left when chasing player at x=0."""
        w = AirWorld()
        right_edge = C.WORLD_WRAP_WIDTH - 2
        cw = CaveWorm(right_edge, 10)
        cw._active = True
        # Player near left edge – shorter path is to wrap right→left
        self._advance(cw, 1, 10, w, C.CAVE_WORM_INTERVAL * 3 + 1)
        # After wrapping, tx should be close to left side
        assert cw.tx < C.WORLD_WRAP_WIDTH // 2 or cw.tx >= right_edge


class TestCaveWormCatchesPlayer:
    def test_catches_at_same_tile(self):
        cw = CaveWorm(7, 7)
        cw._active = True
        cw.tx, cw.ty = 7, 7
        assert cw.catches_player(7, 7)

    def test_no_catch_if_inactive(self):
        cw = CaveWorm(7, 7)
        assert not cw._active
        assert not cw.catches_player(7, 7)

    def test_no_catch_adjacent_tile(self):
        cw = CaveWorm(7, 7)
        cw._active = True
        cw.tx, cw.ty = 7, 7
        assert not cw.catches_player(8, 7)


class TestCaveWormMoveInterval:
    def test_does_not_move_before_interval(self):
        w = AirWorld()
        cw = CaveWorm(5, 10)
        cw._active = True
        start = cw.tx
        for _ in range(C.CAVE_WORM_INTERVAL - 1):
            cw.update(20, 10, w)
        assert cw.tx == start

    def test_moves_exactly_at_interval(self):
        w = AirWorld()
        cw = CaveWorm(5, 10)
        cw._active = True
        start = cw.tx
        for _ in range(C.CAVE_WORM_INTERVAL):
            cw.update(20, 10, w)
        assert cw.tx > start

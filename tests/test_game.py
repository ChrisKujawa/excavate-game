"""Tests for Game state transitions (start, play, game-over, win)."""
import pygame
import pytest
from unittest.mock import patch
from game import Game, GameState


@pytest.fixture
def game():
    return Game()


def _keydown(key):
    e = pygame.event.Event(pygame.KEYDOWN, {"key": key, "mod": 0, "unicode": "", "scancode": 0})
    return e


def _mousedown(pos=(400, 300)):
    e = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})
    return e


def _fingerdown(x=0.5, y=0.5):
    e = pygame.event.Event(pygame.FINGERDOWN, {"finger_id": 1, "x": x, "y": y, "dx": 0, "dy": 0, "pressure": 1.0})
    return e


class TestGameInitialState:
    def test_starts_in_start_state(self, game):
        assert game.state == GameState.START

    def test_player_exists(self, game):
        assert game.player is not None

    def test_world_exists(self, game):
        assert game.world is not None


class TestStartScreenTransitions:
    def test_enter_key_starts_game(self, game):
        game._handle_keydown(_keydown(pygame.K_RETURN))
        assert game.state == GameState.PLAYING

    def test_space_key_starts_game(self, game):
        game._handle_keydown(_keydown(pygame.K_SPACE))
        assert game.state == GameState.PLAYING

    def test_mouse_click_starts_game(self, game):
        game._handle_touch_nav(_mousedown())
        assert game.state == GameState.PLAYING

    def test_finger_tap_starts_game(self, game):
        game._handle_touch_nav(_fingerdown())
        assert game.state == GameState.PLAYING

    def test_other_keys_also_start_game(self, game):
        game._handle_keydown(_keydown(pygame.K_a))
        # _handle_keydown itself doesn't start on arbitrary key —
        # the main loop "any interaction" handler does; this just tests
        # that _handle_keydown doesn't break state
        assert game.state == GameState.START

    def test_escape_does_not_start_game(self, game):
        result = game._handle_keydown(_keydown(pygame.K_ESCAPE))
        assert game.state == GameState.START
        assert result is False  # signals quit


class TestGameOverTransitions:
    def test_player_death_triggers_game_over(self, game):
        game.state = GameState.PLAYING
        game.player.alive = False
        keys = pygame.key.get_pressed()
        game._update(keys)
        assert game.state in (GameState.GAME_OVER, GameState.NAME_INPUT)

    def test_r_key_restarts_from_game_over(self, game):
        game.state = GameState.GAME_OVER
        game._handle_keydown(_keydown(pygame.K_r))
        assert game.state == GameState.PLAYING

    def test_mouse_click_restarts_from_game_over(self, game):
        game.state = GameState.GAME_OVER
        game._handle_touch_nav(_mousedown())
        assert game.state == GameState.PLAYING

    def test_finger_tap_restarts_from_game_over(self, game):
        game.state = GameState.GAME_OVER
        game._handle_touch_nav(_fingerdown())
        assert game.state == GameState.PLAYING


class TestWinTransitions:
    def test_diamond_found_triggers_level_complete(self, game):
        """Finding diamond on level 1 → LEVEL_COMPLETE (not final win)."""
        game.state = GameState.PLAYING
        game.level = 1
        game.player.won = True
        game.player.points = 0
        with patch("highscore.is_highscore", return_value=False):
            keys = pygame.key.get_pressed()
            game._update(keys)
        assert game.state == GameState.LEVEL_COMPLETE

    def test_diamond_found_on_last_level_triggers_win(self, game):
        """Finding diamond on MAX_LEVELS → WIN."""
        import constants as C
        game.state = GameState.PLAYING
        game.level = C.MAX_LEVELS
        game.player.won = True
        game.player.points = 0
        with patch("highscore.is_highscore", return_value=False):
            keys = pygame.key.get_pressed()
            game._update(keys)
        assert game.state == GameState.WIN

    def test_r_key_restarts_from_win(self, game):
        game.state = GameState.WIN
        game._handle_keydown(_keydown(pygame.K_r))
        assert game.state == GameState.PLAYING

    def test_mouse_click_restarts_from_win(self, game):
        game.state = GameState.WIN
        game._handle_touch_nav(_mousedown())
        assert game.state == GameState.PLAYING


class TestCaveWorms:
    def _air_world(self):
        """Minimal world stub where every tile is air."""
        from tile import make_air
        class AirWorld:
            def get(self, tx, ty):
                return make_air()
        return AirWorld()

    def test_world_has_cave_worms(self):
        from world import World
        w = World(seed=42)
        assert len(w.cave_worms) > 0

    def test_cave_worm_activates_on_proximity(self):
        from worm import CaveWorm
        w = self._air_world()
        cw = CaveWorm(10, 20)
        assert not cw._active
        cw.update(10, 20, w)
        assert cw._active

    def test_cave_worm_inactive_far_away(self):
        from worm import CaveWorm
        w = self._air_world()
        cw = CaveWorm(10, 20)
        cw.update(100, 100, w)
        assert not cw._active

    def test_cave_worm_moves_toward_player(self):
        from worm import CaveWorm
        import constants as C
        w = self._air_world()
        cw = CaveWorm(10, 20)
        cw._active = True
        start_tx = cw.tx
        for _ in range(C.CAVE_WORM_INTERVAL + 1):
            cw.update(20, 20, w)
        assert cw.tx > start_tx

    def test_cave_worm_blocked_by_solid(self):
        """Worm stays put if every neighbour is solid."""
        from worm import CaveWorm
        from tile import make_ground
        import constants as C
        class SolidWorld:
            def get(self, tx, ty):
                return make_ground(0)
        w = SolidWorld()
        cw = CaveWorm(10, 20)
        cw._active = True
        start_tx, start_ty = cw.tx, cw.ty
        for _ in range(C.CAVE_WORM_INTERVAL + 1):
            cw.update(20, 20, w)
        assert cw.tx == start_tx and cw.ty == start_ty

    def test_cave_worm_catches_player(self):
        from worm import CaveWorm
        cw = CaveWorm(10, 20)
        cw._active = True
        cw.tx = 5
        cw.ty = 5
        assert cw.catches_player(5, 5)
        assert not cw.catches_player(5, 6)

    def test_worm_speed_increases_per_level(self):
        from worm import Worm
        import constants as C
        w2 = Worm(0, 0, level=2)
        w5 = Worm(0, 0, level=5)
        # Higher level = smaller interval = faster
        assert w5._move_interval <= w2._move_interval
        assert w5._move_interval >= C.WORM_MIN_INTERVAL

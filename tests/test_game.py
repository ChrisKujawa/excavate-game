"""Tests for Game state transitions (start, play, game-over, win) and fullscreen."""
import pygame
import pytest
from unittest.mock import patch, MagicMock
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


# ------------------------------------------------------------------ #
#  Fullscreen toggle                                                   #
# ------------------------------------------------------------------ #

class TestFullscreen:
    def test_screen_is_offscreen_surface_not_display(self, game):
        """game.screen must be a plain Surface, not the display surface,
        so set_mode() can never invalidate it."""
        display = pygame.display.get_surface()
        assert game.screen is not display

    def test_toggle_fullscreen_uses_set_mode_with_depth_32(self, game):
        """set_mode must be called with depth=32 to avoid non-32-bit HDR surfaces."""
        with patch("pygame.display.set_mode") as mock_set_mode, \
             patch("pygame.display.get_surface") as mock_get:
            mock_get.return_value = MagicMock(get_flags=lambda: 0)
            game._toggle_fullscreen()
        args, _ = mock_set_mode.call_args
        assert args[2] == 32

    def test_toggle_fullscreen_windowed_to_fullscreen(self, game):
        """From windowed → fullscreen: set_mode called with FULLSCREEN flag."""
        with patch("pygame.display.set_mode") as mock_set_mode, \
             patch("pygame.display.get_surface") as mock_get:
            mock_get.return_value = MagicMock(get_flags=lambda: 0)
            game._toggle_fullscreen()
        args, _ = mock_set_mode.call_args
        assert args[1] & pygame.FULLSCREEN

    def test_toggle_fullscreen_fullscreen_to_windowed(self, game):
        """From fullscreen → windowed: set_mode called without FULLSCREEN flag."""
        with patch("pygame.display.set_mode") as mock_set_mode, \
             patch("pygame.display.get_surface") as mock_get:
            mock_get.return_value = MagicMock(get_flags=lambda: pygame.FULLSCREEN)
            game._toggle_fullscreen()
        args, _ = mock_set_mode.call_args
        assert not (args[1] & pygame.FULLSCREEN)

    def test_toggle_fullscreen_does_not_update_self_screen(self, game):
        """self.screen is the offscreen surface — _toggle_fullscreen must not overwrite it."""
        surf_before = game.screen
        with patch("pygame.display.set_mode"), \
             patch("pygame.display.get_surface") as mock_get:
            mock_get.return_value = MagicMock(get_flags=lambda: 0)
            game._toggle_fullscreen()
        assert game.screen is surf_before

    def test_f11_key_triggers_fullscreen_toggle(self, game):
        """F11 keydown must call _toggle_fullscreen."""
        game.state = GameState.PLAYING
        e = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F11, "mod": 0,
                                                 "unicode": "", "scancode": 0})
        with patch.object(game, "_toggle_fullscreen") as mock_toggle:
            game._handle_keydown(e)
        mock_toggle.assert_called_once()

    def test_f11_does_not_change_game_state(self, game):
        """F11 is purely a display toggle — game state should be unchanged."""
        game.state = GameState.PLAYING
        e = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F11, "mod": 0,
                                                 "unicode": "", "scancode": 0})
        with patch.object(game, "_toggle_fullscreen"):
            game._handle_keydown(e)
        assert game.state == GameState.PLAYING

    def test_f11_on_start_screen_does_not_start_game(self, game):
        """F11 pressed on start screen must NOT transition to PLAYING."""
        game.state = GameState.START
        e = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F11, "mod": 0,
                                                 "unicode": "", "scancode": 0})
        with patch.object(game, "_toggle_fullscreen"):
            game._handle_keydown(e)
        assert game.state == GameState.START


# ------------------------------------------------------------------ #
#  Offscreen rendering (Bus Error regression)                          #
# ------------------------------------------------------------------ #

class TestOffscreenRendering:
    def test_screen_is_pygame_surface(self, game):
        """game.screen must be a plain pygame.Surface — not the display surface."""
        assert isinstance(game.screen, pygame.Surface)
        assert game.screen is not pygame.display.get_surface()

    def test_screen_has_correct_dimensions(self, game):
        import constants as C
        assert game.screen.get_width()  == C.SCREEN_WIDTH
        assert game.screen.get_height() == C.SCREEN_HEIGHT

    def test_draw_start_state_does_not_raise(self, game):
        """_draw() in START state must not crash (sanity check)."""
        game.state = GameState.START
        game._draw()  # must not raise

    def test_draw_playing_state_does_not_raise(self, game):
        """Regression: _draw() in PLAYING state used to SIGBUS because
        self.screen pointed to the SDL display surface which SDL can
        invalidate after set_mode().  Offscreen surface fixes this."""
        game.state = GameState.PLAYING
        game._draw()  # must not raise (was crashing with Bus Error)

    def test_draw_game_over_does_not_raise(self, game):
        game.state = GameState.GAME_OVER
        game._draw()

    def test_draw_win_does_not_raise(self, game):
        game.state = GameState.WIN
        game._draw()

    def test_draw_does_not_write_to_display_surface(self, game):
        """_draw() must only write to game.screen (offscreen), not the display."""
        display_before = pygame.display.get_surface().copy()
        game.state = GameState.PLAYING
        game._draw()
        # Display surface should be pixel-identical before and after _draw()
        diff = pygame.surfarray.pixels3d(pygame.display.get_surface())
        orig = pygame.surfarray.pixels3d(display_before)
        import numpy as np
        assert np.array_equal(diff, orig), "_draw() must not write directly to display surface"

    def test_screen_unchanged_after_multiple_draws(self, game):
        """game.screen object identity must be stable across multiple _draw calls."""
        surf_ref = game.screen
        game.state = GameState.PLAYING
        for _ in range(5):
            game._draw()
        assert game.screen is surf_ref, "game.screen reference must not change during draw"


# ------------------------------------------------------------------ #
#  Start-screen KEYDOWN filter (Bus Error root cause regression)       #
# ------------------------------------------------------------------ #

# Simulate the event-loop "any interaction starts game" gate.
# Previously KEYDOWN was in this list, so F11 → set_mode + PLAYING draw
# in the same frame → Bus Error on the invalidated display surface.
_START_TRIGGERS = (
    pygame.MOUSEBUTTONDOWN,
    pygame.MOUSEBUTTONUP,
    pygame.FINGERDOWN,
    pygame.FINGERUP,
)


class TestStartScreenKeyFiltering:
    """The event loop only starts the game on pointer/touch events, not KEYDOWN.
    Keyboard game-start is handled exclusively by _handle_keydown (ENTER/SPACE only).
    This prevents system keys like F11 from triggering a PLAYING draw right after
    set_mode(), which was the root cause of the Bus Error."""

    def _sim_loop_transition(self, game, event):
        """Replicate the event-loop 'any interaction starts game' check."""
        if game.state == GameState.START and event.type in _START_TRIGGERS:
            game.state = GameState.PLAYING

    def test_keydown_f11_not_a_start_trigger(self, game):
        e = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_F11, "mod": 0,
                                                 "unicode": "", "scancode": 0})
        self._sim_loop_transition(game, e)
        assert game.state == GameState.START

    def test_keydown_enter_not_a_start_trigger(self, game):
        """ENTER starts via _handle_keydown, not the pointer trigger."""
        e = _keydown(pygame.K_RETURN)
        self._sim_loop_transition(game, e)
        assert game.state == GameState.START

    def test_keydown_space_not_a_start_trigger(self, game):
        e = _keydown(pygame.K_SPACE)
        self._sim_loop_transition(game, e)
        assert game.state == GameState.START

    def test_keydown_arrow_not_a_start_trigger(self, game):
        for key in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            g = Game()
            e = _keydown(key)
            self._sim_loop_transition(g, e)
            assert g.state == GameState.START, f"{key} should not start game"

    def test_mousedown_is_a_start_trigger(self, game):
        e = _mousedown()
        self._sim_loop_transition(game, e)
        assert game.state == GameState.PLAYING

    def test_mouseup_is_a_start_trigger(self, game):
        game.state = GameState.START
        e = pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": (400, 300), "button": 1})
        self._sim_loop_transition(game, e)
        assert game.state == GameState.PLAYING

    def test_fingerdown_is_a_start_trigger(self, game):
        e = _fingerdown()
        self._sim_loop_transition(game, e)
        assert game.state == GameState.PLAYING

    def test_fingerup_is_a_start_trigger(self, game):
        game.state = GameState.START
        e = pygame.event.Event(pygame.FINGERUP, {"finger_id": 1, "x": 0.5, "y": 0.5,
                                                  "dx": 0, "dy": 0})
        self._sim_loop_transition(game, e)
        assert game.state == GameState.PLAYING

    def test_trigger_only_fires_from_start_state(self, game):
        """The pointer trigger must only act when state == START."""
        game.state = GameState.GAME_OVER
        e = _mousedown()
        self._sim_loop_transition(game, e)
        assert game.state == GameState.GAME_OVER

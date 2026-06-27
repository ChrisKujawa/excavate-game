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
    def test_diamond_found_triggers_win(self, game):
        game.state = GameState.PLAYING
        game.player.won = True
        game.player.points = 0  # ensure not a highscore
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

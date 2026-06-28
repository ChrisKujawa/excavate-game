"""Tests für camera.py und highscore.py."""
import pytest
import pygame
import tempfile
import os
from camera import Camera
import constants as C


class TestCamera:
    def test_initial_offset_zero(self):
        cam = Camera()
        assert cam.offset_y == 0.0
        assert cam.offset_x == 0.0

    def test_visible_range_at_top(self):
        cam = Camera()
        first, last = cam.visible_tile_range()
        assert first == 0
        assert last > 0

    def test_apply_shifts_rect_vertically(self):
        cam = Camera()
        cam.offset_y = 100.0
        rect = pygame.Rect(0, 200, 32, 32)
        result = cam.apply(rect)
        assert result.y == 200 - 100

    def test_apply_shifts_rect_horizontally(self):
        cam = Camera()
        cam.offset_x = 64.0
        rect = pygame.Rect(200, 0, 32, 32)
        result = cam.apply(rect)
        assert result.x == 200 - 64

    def test_camera_follows_player_downward(self):
        cam = Camera()
        player_rect = pygame.Rect(0, C.SCREEN_HEIGHT * 2, 24, 28)
        cam.update(player_rect)
        assert cam.offset_y > 0

    def test_camera_follows_player_right(self):
        cam = Camera()
        player_rect = pygame.Rect(C.SCREEN_WIDTH * 3, 0, 24, 28)
        cam.update(player_rect)
        assert cam.offset_x > 0

    def test_camera_never_goes_above_zero(self):
        cam = Camera()
        player_rect = pygame.Rect(0, 0, 24, 28)
        for _ in range(10):
            cam.update(player_rect)
        assert cam.offset_y >= 0

    def test_camera_follows_deep_player(self):
        """Camera scrolls down with player deep in infinite world."""
        cam = Camera()
        player_rect = pygame.Rect(0, 10000, 24, 28)
        for _ in range(20):
            cam.update(player_rect)
        assert cam.offset_y > 0

    def test_world_to_screen_y(self):
        cam = Camera()
        cam.offset_y = 64.0
        assert cam.world_to_screen_y(128) == 64

    def test_world_to_screen_x(self):
        cam = Camera()
        cam.offset_x = 32.0
        assert cam.world_to_screen_x(96) == 64

    def test_visible_col_range(self):
        cam = Camera()
        cam.offset_x = 0.0
        first, last = cam.visible_col_range()
        assert last - first >= C.SCREEN_WIDTH // C.TILE_SIZE

    # ------------------------------------------------------------------ #
    #  Camera uses constants — not pygame.display.get_surface()           #
    # ------------------------------------------------------------------ #

    def test_visible_tile_range_independent_of_display_size(self):
        """visible_tile_range() must use C.SCREEN_HEIGHT, not the display surface."""
        from unittest.mock import patch, MagicMock
        cam = Camera()
        # Pretend the display is twice as tall as the game surface
        fake_display = MagicMock()
        fake_display.get_height.return_value = C.SCREEN_HEIGHT * 2
        fake_display.get_width.return_value  = C.SCREEN_WIDTH  * 2
        with patch("pygame.display.get_surface", return_value=fake_display):
            first, last = cam.visible_tile_range()
        expected_span = C.SCREEN_HEIGHT // C.TILE_SIZE + 3
        assert (last - first) <= expected_span + 2   # stays near constant, not 2×

    def test_visible_col_range_independent_of_display_size(self):
        """visible_col_range() must use C.SCREEN_WIDTH, not the display surface."""
        from unittest.mock import patch, MagicMock
        cam = Camera()
        fake_display = MagicMock()
        fake_display.get_height.return_value = C.SCREEN_HEIGHT * 2
        fake_display.get_width.return_value  = C.SCREEN_WIDTH  * 2
        with patch("pygame.display.get_surface", return_value=fake_display):
            first, last = cam.visible_col_range()
        expected_span = C.SCREEN_WIDTH // C.TILE_SIZE + 3
        assert (last - first) <= expected_span + 2

    def test_update_centers_on_constant_screen_size(self):
        """Camera target is based on C.SCREEN_WIDTH/HEIGHT, not the display surface."""
        from unittest.mock import patch, MagicMock
        cam = Camera()
        # Player exactly at screen centre — camera offset should converge toward 0
        player_rect = pygame.Rect(C.SCREEN_WIDTH // 2, C.SCREEN_HEIGHT // 2, 24, 28)
        fake_display = MagicMock()
        fake_display.get_width.return_value  = C.SCREEN_WIDTH  * 3
        fake_display.get_height.return_value = C.SCREEN_HEIGHT * 3
        with patch("pygame.display.get_surface", return_value=fake_display):
            for _ in range(30):
                cam.update(player_rect)
        # offset_y should stay near 0 (not grow to ~1080 as it would if using display H)
        assert cam.offset_y < C.SCREEN_HEIGHT


# ------------------------------------------------------------------ #
#  Highscore Tests                                                     #
# ------------------------------------------------------------------ #

@pytest.fixture
def hs_module(tmp_path, monkeypatch):
    """Importiert highscore-Modul mit temporärer Datei."""
    import highscore
    monkeypatch.setattr(highscore, "HIGHSCORE_FILE", str(tmp_path / "scores.json"))
    return highscore


class TestHighscore:
    def test_load_empty(self, hs_module):
        assert hs_module.load() == []

    def test_save_and_load(self, hs_module):
        hs_module.save("Alice", 500)
        scores = hs_module.load()
        assert len(scores) == 1
        assert scores[0]["name"] == "Alice"
        assert scores[0]["points"] == 500

    def test_sorted_descending(self, hs_module):
        hs_module.save("Alice", 100)
        hs_module.save("Bob", 500)
        hs_module.save("Carol", 300)
        scores = hs_module.load()
        points = [s["points"] for s in scores]
        assert points == sorted(points, reverse=True)

    def test_max_entries(self, hs_module):
        for i in range(10):
            hs_module.save(f"Player{i}", i * 100)
        assert len(hs_module.load()) <= hs_module.MAX_ENTRIES

    def test_is_highscore_empty_list(self, hs_module):
        assert hs_module.is_highscore(1) is True

    def test_is_highscore_beats_last(self, hs_module):
        for i in range(hs_module.MAX_ENTRIES):
            hs_module.save(f"P{i}", (i + 1) * 100)
        # Niedrigster Score ist 100, 50 wäre kein Highscore
        assert hs_module.is_highscore(50) is False
        assert hs_module.is_highscore(9999) is True

    def test_name_truncated_to_12(self, hs_module):
        hs_module.save("A" * 20, 100)
        scores = hs_module.load()
        assert len(scores[0]["name"]) <= 12

    def test_corrupt_file_returns_empty(self, hs_module):
        with open(hs_module.HIGHSCORE_FILE, "w") as f:
            f.write("not valid json {{")
        assert hs_module.load() == []

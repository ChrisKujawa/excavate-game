"""Tests for TouchControls — layout, event handling, draw (regression for NameError)."""
import pygame
import pytest
from unittest.mock import patch, MagicMock
from touch_controls import TouchControls, _BAR_H


@pytest.fixture
def tc():
    return TouchControls()


# ------------------------------------------------------------------ #
#  Layout                                                              #
# ------------------------------------------------------------------ #

class TestLayout:
    def test_layout_sets_all_button_rects(self, tc):
        tc._update_layout(800, 600)
        for btn in tc.buttons:
            assert btn.rect.width > 0
            assert btn.rect.height > 0

    def test_buttons_inside_control_bar(self, tc):
        W, H = 800, 600
        tc._update_layout(W, H)
        bar_top = H - _BAR_H
        for btn in tc.buttons:
            assert btn.rect.top >= bar_top, f"{btn.action} rect.top above bar"
            assert btn.rect.bottom <= H, f"{btn.action} rect.bottom below screen"

    def test_left_cluster_on_left_half(self, tc):
        tc._update_layout(800, 600)
        left_btn  = next(b for b in tc.buttons if b.action == "left")
        right_btn = next(b for b in tc.buttons if b.action == "right")
        assert left_btn.rect.centerx < 400
        assert right_btn.rect.centerx < 400

    def test_right_cluster_on_right_half(self, tc):
        tc._update_layout(800, 600)
        dig_btn  = next(b for b in tc.buttons if b.action == "dig_down")
        jump_btn = next(b for b in tc.buttons if b.action == "jump")
        assert dig_btn.rect.centerx  > 400
        assert jump_btn.rect.centerx > 400

    def test_layout_cached_no_recalc(self, tc):
        tc._update_layout(800, 600)
        rect_before = tc.buttons[0].rect.copy()
        tc._update_layout(800, 600)
        assert tc.buttons[0].rect == rect_before

    def test_layout_updates_on_resize(self, tc):
        tc._update_layout(800, 600)
        rect_800 = tc.buttons[0].rect.copy()
        tc._update_layout(1280, 720)
        assert tc.buttons[0].rect != rect_800

    def test_button_width_clamps_minimum(self, tc):
        # Narrow screen — buttons shouldn't go below 72px wide
        tc._update_layout(300, 600)
        for btn in tc.buttons:
            assert btn.rect.width >= 72

    def test_button_width_clamps_maximum(self, tc):
        # Wide screen — buttons shouldn't exceed 110px wide
        tc._update_layout(4000, 2000)
        for btn in tc.buttons:
            assert btn.rect.width <= 110


# ------------------------------------------------------------------ #
#  Event handling                                                      #
# ------------------------------------------------------------------ #

class TestEventHandling:
    def _mousedown(self, pos):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})

    def _mouseup(self, pos):
        return pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": pos, "button": 1})

    def _fingerdown(self, fid, x, y):
        return pygame.event.Event(pygame.FINGERDOWN,
                                  {"finger_id": fid, "x": x, "y": y, "dx": 0, "dy": 0})

    def _fingerup(self, fid):
        return pygame.event.Event(pygame.FINGERUP,
                                  {"finger_id": fid, "x": 0, "y": 0, "dx": 0, "dy": 0})

    def _fingermotion(self, fid, x, y):
        return pygame.event.Event(pygame.FINGERMOTION,
                                  {"finger_id": fid, "x": x, "y": y, "dx": 0, "dy": 0})

    def test_mouse_press_on_left_button_marks_pressed(self, tc):
        tc._update_layout(800, 600)
        left_btn = next(b for b in tc.buttons if b.action == "left")
        tc.handle_event(self._mousedown(left_btn.rect.center))
        assert left_btn.pressed

    def test_mouse_release_clears_pressed(self, tc):
        tc._update_layout(800, 600)
        left_btn = next(b for b in tc.buttons if b.action == "left")
        tc.handle_event(self._mousedown(left_btn.rect.center))
        tc.handle_event(self._mouseup(left_btn.rect.center))
        assert not left_btn.pressed

    def test_finger_down_marks_button_pressed(self, tc):
        W, H = 800, 600
        tc._update_layout(W, H)
        left_btn = next(b for b in tc.buttons if b.action == "left")
        cx, cy = left_btn.rect.center
        tc.handle_event(self._fingerdown(1, cx / W, cy / H))
        assert left_btn.pressed

    def test_finger_up_clears_pressed(self, tc):
        W, H = 800, 600
        tc._update_layout(W, H)
        left_btn = next(b for b in tc.buttons if b.action == "left")
        cx, cy = left_btn.rect.center
        tc.handle_event(self._fingerdown(1, cx / W, cy / H))
        tc.handle_event(self._fingerup(1))
        assert not left_btn.pressed

    def test_fingermotion_updates_position(self, tc):
        W, H = 800, 600
        tc._update_layout(W, H)
        right_btn = next(b for b in tc.buttons if b.action == "right")
        left_btn  = next(b for b in tc.buttons if b.action == "left")
        # Start on left button
        lx, ly = left_btn.rect.center
        tc.handle_event(self._fingerdown(1, lx / W, ly / H))
        assert left_btn.pressed
        # Move to right button
        rx, ry = right_btn.rect.center
        tc.handle_event(self._fingermotion(1, rx / W, ry / H))
        assert right_btn.pressed

    def test_mouse_outside_buttons_presses_nothing(self, tc):
        tc._update_layout(800, 600)
        tc.handle_event(self._mousedown((400, 10)))  # top-centre, no button there
        assert not any(b.pressed for b in tc.buttons)


# ------------------------------------------------------------------ #
#  is_held / consume_just_pressed                                     #
# ------------------------------------------------------------------ #

class TestHeldAndOneshot:
    def _mousedown(self, pos):
        return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})

    def _mouseup(self, pos):
        return pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": pos, "button": 1})

    def test_is_held_true_while_pressed(self, tc):
        tc._update_layout(800, 600)
        left_btn = next(b for b in tc.buttons if b.action == "left")
        tc.handle_event(self._mousedown(left_btn.rect.center))
        assert tc.is_held("left")

    def test_is_held_false_after_release(self, tc):
        tc._update_layout(800, 600)
        left_btn = next(b for b in tc.buttons if b.action == "left")
        tc.handle_event(self._mousedown(left_btn.rect.center))
        tc.handle_event(self._mouseup(left_btn.rect.center))
        assert not tc.is_held("left")

    def test_jump_fires_oneshot_on_press(self, tc):
        tc._update_layout(800, 600)
        jump_btn = next(b for b in tc.buttons if b.action == "jump")
        tc.handle_event(self._mousedown(jump_btn.rect.center))
        assert "jump" in tc.consume_just_pressed()

    def test_jump_oneshot_not_repeated_while_held(self, tc):
        tc._update_layout(800, 600)
        jump_btn = next(b for b in tc.buttons if b.action == "jump")
        tc.handle_event(self._mousedown(jump_btn.rect.center))
        tc.consume_just_pressed()  # consume the first press
        # Simulate another frame with button still held (no new press event)
        tc.handle_event(self._mousedown(jump_btn.rect.center))
        assert "jump" not in tc.consume_just_pressed()

    def test_consume_clears_set(self, tc):
        tc._update_layout(800, 600)
        jump_btn = next(b for b in tc.buttons if b.action == "jump")
        tc.handle_event(self._mousedown(jump_btn.rect.center))
        tc.consume_just_pressed()
        assert len(tc.consume_just_pressed()) == 0

    def test_left_is_held_not_oneshot(self, tc):
        tc._update_layout(800, 600)
        left_btn = next(b for b in tc.buttons if b.action == "left")
        tc.handle_event(self._mousedown(left_btn.rect.center))
        # Held actions don't appear in just_pressed
        assert "left" not in tc.consume_just_pressed()


# ------------------------------------------------------------------ #
#  draw() — regression: sub_surf must not be used before assignment   #
# ------------------------------------------------------------------ #

class TestDraw:
    def test_draw_does_not_raise(self, tc):
        """Regression: NameError 'sub_surf' used before assignment crashed every PLAYING frame."""
        surface = pygame.display.get_surface()
        tc._update_layout(*surface.get_size())
        tc.draw(surface)  # must not raise

    def test_draw_with_button_pressed_does_not_raise(self, tc):
        surface = pygame.display.get_surface()
        tc._update_layout(*surface.get_size())
        # Force all buttons pressed
        for btn in tc.buttons:
            btn.pressed = True
        tc.draw(surface)

    def test_draw_updates_layout_from_surface(self, tc):
        """draw() should call _update_layout so layout is always in sync with surface size."""
        surface = pygame.display.get_surface()
        # Reset cached layout so _update_layout must run
        tc._layout_wh = (0, 0)
        tc.draw(surface)
        assert tc._layout_wh == surface.get_size()

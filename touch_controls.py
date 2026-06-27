import pygame
import constants as C

_BTN = 80
_PAD = 10


class _Button:
    def __init__(self, rect, label, action):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.pressed = False


class TouchControls:
    """On-screen buttons for touch / mobile play."""

    # Actions that stay active while held
    HELD = {"left", "right"}
    # Actions that fire once on press
    ONESHOT = {"jump", "dig_down"}

    def __init__(self):
        W, H = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        y = H - _BTN - _PAD
        self.buttons = [
            _Button((_PAD,               y, _BTN, _BTN), "◀", "left"),
            _Button((_PAD + _BTN + _PAD, y, _BTN, _BTN), "▶", "right"),
            _Button((W - _PAD - _BTN * 2 - _PAD, y, _BTN, _BTN), "⬇", "dig_down"),
            _Button((W - _PAD - _BTN,            y, _BTN, _BTN), "↑", "jump"),
        ]
        self._touches: dict = {}       # finger_id/mouse → (x, y)
        self._prev: dict = {b.action: False for b in self.buttons}
        self._just_pressed: set = set()
        self._font = None

    def _font_cached(self):
        if self._font is None:
            self._font = pygame.font.SysFont("monospace", 30, bold=True)
        return self._font

    # ------------------------------------------------------------------ #
    #  Event handling                                                      #
    # ------------------------------------------------------------------ #

    def handle_event(self, event):
        if event.type == pygame.FINGERDOWN:
            self._touches[event.finger_id] = (
                int(event.x * C.SCREEN_WIDTH),
                int(event.y * C.SCREEN_HEIGHT),
            )
        elif event.type == pygame.FINGERUP:
            self._touches.pop(event.finger_id, None)
        elif event.type == pygame.FINGERMOTION:
            self._touches[event.finger_id] = (
                int(event.x * C.SCREEN_WIDTH),
                int(event.y * C.SCREEN_HEIGHT),
            )
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._touches["mouse"] = event.pos
        elif event.type == pygame.MOUSEBUTTONUP:
            self._touches.pop("mouse", None)
        elif event.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[0]:
                self._touches["mouse"] = event.pos
            else:
                self._touches.pop("mouse", None)

        # Refresh button states
        for btn in self.buttons:
            btn.pressed = any(
                btn.rect.collidepoint(pos) for pos in self._touches.values()
            )

        # Detect rising edge for one-shot actions
        for btn in self.buttons:
            if btn.action in self.ONESHOT and btn.pressed and not self._prev[btn.action]:
                self._just_pressed.add(btn.action)
        self._prev = {b.action: b.pressed for b in self.buttons}

    def consume_just_pressed(self) -> set:
        """Return and clear one-shot actions triggered this frame."""
        result = self._just_pressed
        self._just_pressed = set()
        return result

    def is_held(self, action: str) -> bool:
        return any(b.pressed for b in self.buttons if b.action == action)

    def any_touch_active(self) -> bool:
        return bool(self._touches)

    # ------------------------------------------------------------------ #
    #  Drawing                                                             #
    # ------------------------------------------------------------------ #

    def draw(self, surface: pygame.Surface):
        font = self._font_cached()
        for btn in self.buttons:
            bg = pygame.Surface((btn.rect.width, btn.rect.height), pygame.SRCALPHA)
            bg.fill((255, 220, 50, 200) if btn.pressed else (60, 60, 60, 140))
            surface.blit(bg, btn.rect.topleft)
            pygame.draw.rect(surface, (200, 200, 200), btn.rect, 2, border_radius=10)
            lbl = font.render(btn.label, True, (255, 255, 255))
            surface.blit(lbl, (
                btn.rect.centerx - lbl.get_width() // 2,
                btn.rect.centery - lbl.get_height() // 2,
            ))

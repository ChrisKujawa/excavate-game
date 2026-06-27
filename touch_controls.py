import pygame
import constants as C

_BAR_H = 115  # height of the dedicated control strip at the bottom


class _Button:
    def __init__(self, direction, sub_label, action):
        self.direction = direction  # "left" | "right" | "up" | "down"
        self.sub_label = sub_label
        self.action    = action
        self.rect      = pygame.Rect(0, 0, 0, 0)
        self.pressed   = False


class TouchControls:
    """On-screen buttons for touch / mobile play."""

    HELD    = {"left", "right"}
    ONESHOT = {"jump", "dig_down"}

    def __init__(self):
        self.buttons = [
            _Button("left",  "LEFT",  "left"),
            _Button("right", "RIGHT", "right"),
            _Button("down",  "DIG",   "dig_down"),
            _Button("up",    "JUMP",  "jump"),
        ]
        self._touches: dict = {}
        self._prev:    dict = {b.action: False for b in self.buttons}
        self._just_pressed: set = set()
        self._font_icon = None
        self._font_sub  = None
        self._layout_wh = (0, 0)

    # ------------------------------------------------------------------ #
    #  Layout                                                              #
    # ------------------------------------------------------------------ #

    def _update_layout(self, W, H):
        if (W, H) == self._layout_wh:
            return
        self._layout_wh = (W, H)

        PAD   = 14
        BTN_W = max(72, min(110, (W // 2 - PAD * 3) // 2))
        BTN_H = _BAR_H - PAD * 2
        y     = H - BTN_H - PAD

        # Left cluster: ◄  ►
        self.buttons[0].rect = pygame.Rect(PAD,               y, BTN_W, BTN_H)
        self.buttons[1].rect = pygame.Rect(PAD * 2 + BTN_W,   y, BTN_W, BTN_H)
        # Right cluster: ▼  ▲
        self.buttons[2].rect = pygame.Rect(W - PAD * 2 - BTN_W * 2, y, BTN_W, BTN_H)
        self.buttons[3].rect = pygame.Rect(W - PAD - BTN_W,          y, BTN_W, BTN_H)

    def _display_size(self):
        s = pygame.display.get_surface()
        return s.get_width(), s.get_height()

    # ------------------------------------------------------------------ #
    #  Fonts (lazy)                                                        #
    # ------------------------------------------------------------------ #

    def _get_fonts(self):
        if self._font_icon is None:
            self._font_icon = pygame.font.SysFont("monospace", 12)
            self._font_sub  = self._font_icon
        return self._font_icon, self._font_sub

    # ------------------------------------------------------------------ #
    #  Event handling                                                      #
    # ------------------------------------------------------------------ #

    def handle_event(self, event):
        W, H = self._display_size()
        self._update_layout(W, H)

        if event.type == pygame.FINGERDOWN:
            self._touches[event.finger_id] = (int(event.x * W), int(event.y * H))
        elif event.type == pygame.FINGERUP:
            self._touches.pop(event.finger_id, None)
        elif event.type == pygame.FINGERMOTION:
            self._touches[event.finger_id] = (int(event.x * W), int(event.y * H))
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._touches["mouse"] = event.pos
        elif event.type == pygame.MOUSEBUTTONUP:
            self._touches.pop("mouse", None)
        elif event.type == pygame.MOUSEMOTION:
            if pygame.mouse.get_pressed()[0]:
                self._touches["mouse"] = event.pos
            else:
                self._touches.pop("mouse", None)

        for btn in self.buttons:
            btn.pressed = any(
                btn.rect.collidepoint(pos) for pos in self._touches.values()
            )

        for btn in self.buttons:
            if btn.action in self.ONESHOT and btn.pressed and not self._prev[btn.action]:
                self._just_pressed.add(btn.action)
        self._prev = {b.action: b.pressed for b in self.buttons}

    def consume_just_pressed(self) -> set:
        result = self._just_pressed
        self._just_pressed = set()
        return result

    def is_held(self, action: str) -> bool:
        return any(b.pressed for b in self.buttons if b.action == action)

    # ------------------------------------------------------------------ #
    #  Drawing                                                             #
    # ------------------------------------------------------------------ #

    def draw(self, surface: pygame.Surface):
        W, H = surface.get_size()
        self._update_layout(W, H)
        f_icon, f_sub = self._get_fonts()

        # Dedicated dark control bar
        bar = pygame.Surface((W, _BAR_H), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 195))
        surface.blit(bar, (0, H - _BAR_H))
        pygame.draw.line(surface, (255, 215, 0), (0, H - _BAR_H), (W, H - _BAR_H), 1)

        for btn in self.buttons:
            if btn.pressed:
                fill   = (255, 215, 0, 240)
                border = (255, 255, 255)
                fg     = (0, 0, 0)
                sub_fg = (30, 30, 30)
            else:
                fill   = (25, 25, 45, 220)
                border = (140, 140, 160)
                fg     = (230, 230, 230)
                sub_fg = (120, 120, 140)

            bg = pygame.Surface((btn.rect.width, btn.rect.height), pygame.SRCALPHA)
            bg.fill(fill)
            surface.blit(bg, btn.rect.topleft)
            pygame.draw.rect(surface, border, btn.rect, 2, border_radius=12)

            # Sub-label (rendered first so its height can position the arrow)
            sub_surf = f_sub.render(btn.sub_label, True, sub_fg)
            sub_x = btn.rect.centerx - sub_surf.get_width() // 2
            sub_y = btn.rect.bottom - sub_surf.get_height() - 5
            surface.blit(sub_surf, (sub_x, sub_y))

            # Arrow triangle (centred in the space above the sub-label)
            cx2 = btn.rect.centerx
            cy2 = btn.rect.top + (btn.rect.height - sub_surf.get_height() - 5) // 2
            s = min(btn.rect.width, btn.rect.height) // 4
            d = btn.direction
            if d == "left":
                pts = [(cx2 - s, cy2), (cx2 + s, cy2 - s), (cx2 + s, cy2 + s)]
            elif d == "right":
                pts = [(cx2 + s, cy2), (cx2 - s, cy2 - s), (cx2 - s, cy2 + s)]
            elif d == "up":
                pts = [(cx2, cy2 - s), (cx2 - s, cy2 + s), (cx2 + s, cy2 + s)]
            else:  # down
                pts = [(cx2, cy2 + s), (cx2 - s, cy2 - s), (cx2 + s, cy2 - s)]
            pygame.draw.polygon(surface, fg, pts)


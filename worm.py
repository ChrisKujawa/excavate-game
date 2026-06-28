import pygame
from collections import deque
import constants as C


# ------------------------------------------------------------------ #
#  Gemeinsame Zeichenroutine                                           #
# ------------------------------------------------------------------ #

def _draw_segments(surface: pygame.Surface, camera, history, head_size: int, color: tuple):
    """Zeichnet einen Wurm als Kette von Kreisen: Schwanz dünn → Kopf dick."""
    segments = list(history)
    if not segments:
        return
    sw, sh = surface.get_width(), surface.get_height()
    n = len(segments)
    head_r = head_size // 2

    for i, (tx, ty) in enumerate(segments):
        sx = camera.world_to_screen_x(tx * C.TILE_SIZE + C.TILE_SIZE // 2)
        sy = camera.world_to_screen_y(ty * C.TILE_SIZE + C.TILE_SIZE // 2)
        if sx < -head_r - 2 or sx > sw + head_r + 2:
            continue
        if sy < -head_r - 2 or sy > sh + head_r + 2:
            continue

        frac   = i / max(1, n - 1)          # 0 = Schwanz, 1 = Kopf
        radius = max(2, int(head_r * (0.35 + 0.65 * frac)))
        seg_color = tuple(min(255, int(c * (0.65 + 0.35 * frac))) for c in color)
        pygame.draw.circle(surface, seg_color, (sx, sy), radius)

    # Kopf-Details: Augen + Glanzpunkt
    head_tx, head_ty = segments[-1]
    hx = camera.world_to_screen_x(head_tx * C.TILE_SIZE + C.TILE_SIZE // 2)
    hy = camera.world_to_screen_y(head_ty * C.TILE_SIZE + C.TILE_SIZE // 2)
    if 0 <= hx <= sw and 0 <= hy <= sh:
        eye_r   = max(2, head_r // 3)
        eye_off = max(2, head_r // 2)
        for ex in (hx - eye_off, hx + eye_off):
            ey = hy - eye_off // 2
            pygame.draw.circle(surface, (255, 230, 80), (ex, ey), eye_r)
            pygame.draw.circle(surface, (0, 0, 0),      (ex, ey), max(1, eye_r - 1))
        pygame.draw.circle(surface, (255, 255, 200),
                           (hx + head_r // 3, hy - head_r // 3),
                           max(1, head_r // 4))


# ------------------------------------------------------------------ #
#  Worm – Trail-Verfolger                                              #
# ------------------------------------------------------------------ #

class Worm:
    """Folgt dem gegrabenen Tunnel des Spielers als langer segmentierter Wurm."""

    def __init__(self, start_tx: int, start_ty: int, level: int = 2):
        self.tx = start_tx
        self.ty = start_ty
        self._trail_index: int = 0
        self._delay: int = C.WORM_START_DELAY
        self._move_counter: int = 0
        levels_active = max(0, level - C.WORM_LEVEL_START)
        interval = C.WORM_MOVE_INTERVAL - levels_active * 2
        self._move_interval: int = max(C.WORM_MIN_INTERVAL, interval)
        self._history: deque = deque(
            [(start_tx, start_ty)] * C.WORM_SEGMENTS,
            maxlen=C.WORM_SEGMENTS,
        )
        self.rect = pygame.Rect(
            start_tx * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2,
            start_ty * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2,
            C.WORM_SIZE, C.WORM_SIZE,
        )

    def update(self, trail: list[tuple[int, int]]):
        if self._delay > 0:
            self._delay -= 1
            return
        if len(trail) <= 1:
            return
        self._move_counter += 1
        if self._move_counter < self._move_interval:
            return
        self._move_counter = 0
        if self._trail_index < len(trail) - 1:
            self._trail_index += 1
        tx, ty = trail[self._trail_index]
        self.tx, self.ty = tx, ty
        self._history.append((tx, ty))
        self.rect.x = tx * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2
        self.rect.y = ty * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2

    def catches_player(self, player_tx: int, player_ty: int) -> bool:
        return self._delay <= 0 and self.tx == player_tx and self.ty == player_ty

    @property
    def is_active(self) -> bool:
        return self._delay <= 0

    @property
    def delay_seconds(self) -> float:
        return self._delay / C.FPS

    def draw(self, surface: pygame.Surface, camera):
        _draw_segments(surface, camera, self._history, C.WORM_SIZE, C.WORM_COLOR)


# ------------------------------------------------------------------ #
#  CaveWorm – Höhlenwurm                                               #
# ------------------------------------------------------------------ #

class CaveWorm:
    """Lauert in leeren Höhlen; bewegt sich nur durch Luft-Tiles."""

    def __init__(self, start_tx: int, start_ty: int):
        self.tx = start_tx
        self.ty = start_ty
        self._active: bool = False
        self._move_counter: int = 0
        self._history: deque = deque(
            [(start_tx, start_ty)] * C.CAVE_WORM_SEGMENTS,
            maxlen=C.CAVE_WORM_SEGMENTS,
        )
        self.rect = pygame.Rect(
            start_tx * C.TILE_SIZE + (C.TILE_SIZE - C.CAVE_WORM_SIZE) // 2,
            start_ty * C.TILE_SIZE + (C.TILE_SIZE - C.CAVE_WORM_SIZE) // 2,
            C.CAVE_WORM_SIZE, C.CAVE_WORM_SIZE,
        )

    def _is_passable(self, tx: int, ty: int, world) -> bool:
        from tile import TileKind
        return world.get(tx % C.WORLD_WRAP_WIDTH, ty).kind == TileKind.AIR

    def update(self, player_tx: int, player_ty: int, world):
        wrap = C.WORLD_WRAP_WIDTH
        dx = player_tx - self.tx
        if abs(dx) > wrap // 2:
            dx -= wrap * (1 if dx > 0 else -1)
        dy = player_ty - self.ty
        if abs(dx) + abs(dy) <= C.CAVE_WORM_DETECT_RADIUS:
            self._active = True
        if not self._active:
            return
        self._move_counter += 1
        if self._move_counter < C.CAVE_WORM_INTERVAL:
            return
        self._move_counter = 0

        dirs = []
        if abs(dx) >= abs(dy):
            if dx != 0: dirs.append(((1 if dx > 0 else -1), 0))
            if dy != 0: dirs.append((0, (1 if dy > 0 else -1)))
        else:
            if dy != 0: dirs.append((0, (1 if dy > 0 else -1)))
            if dx != 0: dirs.append(((1 if dx > 0 else -1), 0))
        for d in [(1,0),(-1,0),(0,1),(0,-1)]:
            if d not in dirs:
                dirs.append(d)

        for ddx, ddy in dirs:
            ntx = (self.tx + ddx) % wrap
            nty = self.ty + ddy
            if self._is_passable(ntx, nty, world):
                self.tx, self.ty = ntx, nty
                self._history.append((ntx, nty))
                self.rect.x = ntx * C.TILE_SIZE + (C.TILE_SIZE - C.CAVE_WORM_SIZE) // 2
                self.rect.y = nty * C.TILE_SIZE + (C.TILE_SIZE - C.CAVE_WORM_SIZE) // 2
                break

    def catches_player(self, player_tx: int, player_ty: int) -> bool:
        return self._active and self.tx == player_tx and self.ty == player_ty

    def draw(self, surface: pygame.Surface, camera):
        _draw_segments(surface, camera, self._history, C.CAVE_WORM_SIZE, C.CAVE_WORM_COLOR)

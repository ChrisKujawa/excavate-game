import pygame
import constants as C


class Worm:
    """Ein Wurm, der ab Level 2 den gegrabenen Tunnel des Spielers verfolgt.

    Der Wurm startet an der Spawn-Position und folgt dem Trail (Liste der
    besuchten Tile-Positionen) des Spielers. Pro Level wird er schneller.
    """

    def __init__(self, start_tx: int, start_ty: int, level: int = 2):
        self.tx = start_tx
        self.ty = start_ty
        self._trail_index: int = 0
        self._delay: int = C.WORM_START_DELAY
        self._move_counter: int = 0
        levels_active = max(0, level - C.WORM_LEVEL_START)
        interval = C.WORM_MOVE_INTERVAL - levels_active * 2
        self._move_interval: int = max(C.WORM_MIN_INTERVAL, interval)
        self.rect = pygame.Rect(
            start_tx * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2,
            start_ty * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2,
            C.WORM_SIZE,
            C.WORM_SIZE,
        )

    def update(self, trail: list[tuple[int, int]]):
        """Einen Schritt im Trail vorwärtsbewegen."""
        if self._delay > 0:
            self._delay -= 1
            return
        if len(trail) <= 1:
            return
        self._move_counter += 1
        if self._move_counter < self._move_interval:
            return
        self._move_counter = 0
        target = len(trail) - 1
        if self._trail_index < target:
            self._trail_index += 1
        tx, ty = trail[self._trail_index]
        self.tx = tx
        self.ty = ty
        self.rect.x = tx * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2
        self.rect.y = ty * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2

    def catches_player(self, player_tx: int, player_ty: int) -> bool:
        if self._delay > 0:
            return False
        return self.tx == player_tx and self.ty == player_ty

    @property
    def is_active(self) -> bool:
        return self._delay <= 0

    @property
    def delay_seconds(self) -> float:
        return self._delay / C.FPS

    def draw(self, surface: pygame.Surface, camera):
        _draw_worm_shape(surface, camera, self.rect, C.WORM_SIZE, C.WORM_COLOR)


class CaveWorm:
    """Ein Höhlenwurm, der in leeren Höhlen lauert und den Spieler direkt verfolgt.

    Sobald der Spieler den Erkennungsradius betritt, erwacht der Wurm und
    jagt den Spieler durch den Untergrund – er bohrt sich durch Gestein!
    """

    def __init__(self, start_tx: int, start_ty: int):
        self.tx = start_tx
        self.ty = start_ty
        self._active: bool = False
        self._move_counter: int = 0
        self.rect = pygame.Rect(
            start_tx * C.TILE_SIZE + (C.TILE_SIZE - C.CAVE_WORM_SIZE) // 2,
            start_ty * C.TILE_SIZE + (C.TILE_SIZE - C.CAVE_WORM_SIZE) // 2,
            C.CAVE_WORM_SIZE,
            C.CAVE_WORM_SIZE,
        )

    def update(self, player_tx: int, player_ty: int):
        # Wrap-bewusste Distanz
        dx = player_tx - self.tx
        wrap = C.WORLD_WRAP_WIDTH
        if abs(dx) > wrap // 2:
            dx -= wrap * (1 if dx > 0 else -1)
        dy = player_ty - self.ty
        dist = abs(dx) + abs(dy)
        if dist <= C.CAVE_WORM_DETECT_RADIUS:
            self._active = True
        if not self._active:
            return

        self._move_counter += 1
        if self._move_counter < C.CAVE_WORM_INTERVAL:
            return
        self._move_counter = 0

        # Einen Schritt in Richtung Spieler
        if abs(dx) >= abs(dy):
            self.tx = (self.tx + (1 if dx > 0 else -1)) % wrap
        elif dy != 0:
            self.ty += 1 if dy > 0 else -1
        self.rect.x = self.tx * C.TILE_SIZE + (C.TILE_SIZE - C.CAVE_WORM_SIZE) // 2
        self.rect.y = self.ty * C.TILE_SIZE + (C.TILE_SIZE - C.CAVE_WORM_SIZE) // 2

    def catches_player(self, player_tx: int, player_ty: int) -> bool:
        if not self._active:
            return False
        return self.tx == player_tx and self.ty == player_ty

    def draw(self, surface: pygame.Surface, camera):
        _draw_worm_shape(surface, camera, self.rect, C.CAVE_WORM_SIZE, C.CAVE_WORM_COLOR)


def _draw_worm_shape(surface, camera, rect, size, color):
    """Gemeinsame Zeichenroutine für alle Wurmarten."""
    screen_rect = camera.apply(rect)
    sw, sh = surface.get_width(), surface.get_height()
    if screen_rect.right < 0 or screen_rect.left > sw:
        return
    if screen_rect.bottom < 0 or screen_rect.top > sh:
        return
    pygame.draw.ellipse(surface, color, screen_rect)
    eye_y = screen_rect.top + screen_rect.height // 3
    eye_r = max(2, size // 8)
    offset = screen_rect.width // 4
    for ex in (screen_rect.centerx - offset, screen_rect.centerx + offset):
        pygame.draw.circle(surface, (255, 220, 0), (ex, eye_y), eye_r)
        pygame.draw.circle(surface, (0, 0, 0),     (ex, eye_y), max(1, eye_r - 1))


import pygame
import constants as C


class Worm:
    """Ein Wurm, der ab Level 3 den gegrabenen Tunnel des Spielers verfolgt.

    Der Wurm startet an der Spawn-Position und folgt dem Trail (Liste der
    besuchten Tile-Positionen) des Spielers. Nach einem konfigurierbaren
    Vorsprung (WORM_START_DELAY Frames) beginnt er sich zu bewegen.
    Wenn er den Spieler einholt, ist das Spiel verloren.
    """

    def __init__(self, start_tx: int, start_ty: int):
        self.tx = start_tx
        self.ty = start_ty
        self._trail_index: int = 0
        self._delay: int = C.WORM_START_DELAY
        self._move_counter: int = 0
        self.rect = pygame.Rect(
            start_tx * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2,
            start_ty * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2,
            C.WORM_SIZE,
            C.WORM_SIZE,
        )

    # ------------------------------------------------------------------ #
    #  Update                                                              #
    # ------------------------------------------------------------------ #

    def update(self, trail: list[tuple[int, int]]):
        """Einen Schritt im Trail vorwärtsbewegen."""
        if self._delay > 0:
            self._delay -= 1
            return
        if len(trail) <= 1:
            return

        self._move_counter += 1
        if self._move_counter < C.WORM_MOVE_INTERVAL:
            return
        self._move_counter = 0

        # Nicht über das Ende des Trails (Spieler-Position) hinausgehen
        target = len(trail) - 1
        if self._trail_index < target:
            self._trail_index += 1

        tx, ty = trail[self._trail_index]
        self.tx = tx
        self.ty = ty
        self.rect.x = tx * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2
        self.rect.y = ty * C.TILE_SIZE + (C.TILE_SIZE - C.WORM_SIZE) // 2

    # ------------------------------------------------------------------ #
    #  Kollision                                                           #
    # ------------------------------------------------------------------ #

    def catches_player(self, player_tx: int, player_ty: int) -> bool:
        """True wenn der Wurm den Spieler erreicht hat."""
        if self._delay > 0:
            return False
        return self.tx == player_tx and self.ty == player_ty

    # ------------------------------------------------------------------ #
    #  Eigenschaften                                                       #
    # ------------------------------------------------------------------ #

    @property
    def is_active(self) -> bool:
        """True sobald der Vorsprung abgelaufen ist."""
        return self._delay <= 0

    @property
    def delay_seconds(self) -> float:
        """Verbleibende Vorsprung-Sekunden."""
        return self._delay / C.FPS

    # ------------------------------------------------------------------ #
    #  Zeichnen                                                            #
    # ------------------------------------------------------------------ #

    def draw(self, surface: pygame.Surface, camera):
        screen_rect = camera.apply(self.rect)
        sw, sh = surface.get_width(), surface.get_height()
        if screen_rect.right < 0 or screen_rect.left > sw:
            return
        if screen_rect.bottom < 0 or screen_rect.top > sh:
            return

        # Körper (Oval)
        pygame.draw.ellipse(surface, C.WORM_COLOR, screen_rect)

        # Augen
        eye_y = screen_rect.top + screen_rect.height // 3
        offset = screen_rect.width // 4
        pygame.draw.circle(surface, (255, 220, 0),
                           (screen_rect.centerx - offset, eye_y), 3)
        pygame.draw.circle(surface, (255, 220, 0),
                           (screen_rect.centerx + offset, eye_y), 3)
        pygame.draw.circle(surface, (0, 0, 0),
                           (screen_rect.centerx - offset, eye_y), 1)
        pygame.draw.circle(surface, (0, 0, 0),
                           (screen_rect.centerx + offset, eye_y), 1)

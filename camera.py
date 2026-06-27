import pygame
import constants as C


class Camera:
    """Verfolgt den Spieler vertikal und berechnet den sichtbaren Bereich."""

    def __init__(self):
        self.offset_y: float = 0.0  # in Pixeln

    def update(self, player_rect: pygame.Rect):
        # Spieler vertikal zentrieren
        target_y = player_rect.centery - C.SCREEN_HEIGHT // 2
        # Sanftes Folgen
        self.offset_y += (target_y - self.offset_y) * (1 - C.CAMERA_LAG)
        # Nicht über den oberen Rand hinaus
        self.offset_y = max(0, self.offset_y)
        # Nicht unter den unteren Rand
        max_offset = C.WORLD_HEIGHT * C.TILE_SIZE - C.SCREEN_HEIGHT
        self.offset_y = min(self.offset_y, max_offset)

    def apply(self, rect: pygame.Rect) -> pygame.Rect:
        """Gibt das Rect mit angewendetem Kamera-Offset zurück."""
        return rect.move(0, -int(self.offset_y))

    def world_to_screen_y(self, world_y: int) -> int:
        return world_y - int(self.offset_y)

    def visible_tile_range(self) -> tuple[int, int]:
        """Gibt erste und letzte sichtbare Tile-Reihe zurück."""
        first = max(0, int(self.offset_y) // C.TILE_SIZE - 1)
        last  = min(C.WORLD_HEIGHT, first + C.SCREEN_HEIGHT // C.TILE_SIZE + 3)
        return first, last

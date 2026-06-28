import constants as C


class Camera:
    """Verfolgt den Spieler horizontal und vertikal."""

    def __init__(self):
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0

    def update(self, player_rect, world=None):
        sw, sh = C.SCREEN_WIDTH, C.SCREEN_HEIGHT

        target_y = player_rect.centery - sh // 2
        self.offset_y += (target_y - self.offset_y) * (1 - C.CAMERA_LAG)
        self.offset_y = max(0, self.offset_y)

        target_x = player_rect.centerx - sw // 2
        self.offset_x += (target_x - self.offset_x) * (1 - C.CAMERA_LAG)

    def apply(self, rect):
        import pygame
        return rect.move(-int(self.offset_x), -int(self.offset_y))

    def world_to_screen_y(self, world_y: int) -> int:
        return world_y - int(self.offset_y)

    def world_to_screen_x(self, world_x: int) -> int:
        return world_x - int(self.offset_x)

    def visible_tile_range(self) -> tuple[int, int]:
        first = max(0, int(self.offset_y) // C.TILE_SIZE - 1)
        last  = first + C.SCREEN_HEIGHT // C.TILE_SIZE + 3
        return first, last

    def visible_col_range(self) -> tuple[int, int]:
        first = int(self.offset_x) // C.TILE_SIZE - 1
        last  = first + C.SCREEN_WIDTH // C.TILE_SIZE + 3
        return first, last

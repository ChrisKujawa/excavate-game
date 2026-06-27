import pygame
import constants as C
from world import World
from player import Player
from camera import Camera
from ui import UI
from tile import TileKind, get_zone_index


class Game:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.clock  = pygame.time.Clock()
        self.ui     = UI()
        self.ui.load_fonts()
        self._new_game()

    def _new_game(self):
        import random
        self.world  = World(seed=random.randint(0, 99999))
        self.player = Player(self.world)
        self.camera = Camera()

    # ------------------------------------------------------------------ #
    #  Haupt-Loop                                                          #
    # ------------------------------------------------------------------ #

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(C.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    self._handle_keydown(event.key)

            keys = pygame.key.get_pressed()
            self._update(keys)
            self._draw()
            pygame.display.flip()

    # ------------------------------------------------------------------ #
    #  Input                                                               #
    # ------------------------------------------------------------------ #

    def _handle_keydown(self, key):
        if key == pygame.K_r:
            self._new_game()
            return

        if not self.player.alive or self.player.won:
            return

        if key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
            self.player.jump()
        if key == pygame.K_DOWN or key == pygame.K_s:
            self.player.try_dig("down")
        if key == pygame.K_q:
            self.player.try_dig("left")
        if key == pygame.K_e:
            self.player.try_dig("right")

    def _update(self, keys):
        if not self.player.alive or self.player.won:
            return
        self.player.update(keys)
        self.camera.update(self.player.rect)

    # ------------------------------------------------------------------ #
    #  Zeichnen                                                            #
    # ------------------------------------------------------------------ #

    def _draw(self):
        self.screen.fill(C.COLOR_SKY)
        self._draw_world()
        self._draw_player()
        self._draw_hud()

    def _draw_world(self):
        first_row, last_row = self.camera.visible_tile_range()

        for ty in range(first_row, last_row):
            screen_y = self.camera.world_to_screen_y(ty * C.TILE_SIZE)
            for tx in range(self.world.width):
                tile = self.world.get(tx, ty)
                if tile.kind == TileKind.AIR:
                    continue
                rect = pygame.Rect(
                    tx * C.TILE_SIZE,
                    screen_y,
                    C.TILE_SIZE,
                    C.TILE_SIZE,
                )
                pygame.draw.rect(self.screen, tile.color, rect)
                # Umrandung für bessere Sichtbarkeit
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

                # Ressourcen und Diamanten etwas heller hervorheben
                if tile.kind in (TileKind.RESOURCE, TileKind.DIAMOND):
                    glow = pygame.Surface((C.TILE_SIZE - 6, C.TILE_SIZE - 6), pygame.SRCALPHA)
                    glow.fill((*tile.color[:3], 80))
                    inner = pygame.Rect(
                        tx * C.TILE_SIZE + 3,
                        screen_y + 3,
                        C.TILE_SIZE - 6,
                        C.TILE_SIZE - 6,
                    )
                    self.screen.blit(glow, inner)

    def _draw_player(self):
        screen_rect = self.camera.apply(self.player.rect)
        pygame.draw.rect(self.screen, C.COLOR_PLAYER, screen_rect, border_radius=4)
        # Augen
        eye_y = screen_rect.top + 6
        pygame.draw.circle(self.screen, C.COLOR_BLACK, (screen_rect.left + 6, eye_y), 3)
        pygame.draw.circle(self.screen, C.COLOR_BLACK, (screen_rect.right - 6, eye_y), 3)

    def _draw_hud(self):
        self.ui.draw_hud(self.screen, self.player)

        # Zone-Name
        zone_idx = get_zone_index(self.player.depth() + 2)
        zone_name = C.ZONES[zone_idx]["name"]
        self.ui.draw_zone_name(self.screen, zone_name)

        if not self.player.alive:
            self.ui.draw_game_over(self.screen, self.player.points)
        elif self.player.won:
            self.ui.draw_win(self.screen, self.player.points)

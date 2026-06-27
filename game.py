import asyncio
import pygame
import constants as C
from world import World
from player import Player
from camera import Camera
from ui import UI
from tile import TileKind, get_zone_index
import highscore as hs


class GameState:
    START      = "start"
    PLAYING    = "playing"
    GAME_OVER  = "game_over"
    WIN        = "win"
    NAME_INPUT = "name_input"


class Game:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.clock  = pygame.time.Clock()
        self.ui     = UI()
        self.ui.load_fonts()
        self.state  = GameState.START
        self.input_name: str = ""
        self._new_game()

    def _new_game(self):
        import random
        self.world  = World(seed=random.randint(0, 99999))
        self.player = Player(self.world)
        self.camera = Camera()
        self.input_name = ""
        self._fluid_tick = 0

    # ------------------------------------------------------------------ #
    #  Haupt-Loop                                                          #
    # ------------------------------------------------------------------ #

    async def run(self):
        running = True
        while running:
            self.clock.tick(C.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    running = self._handle_keydown(event)
                if event.type == pygame.TEXTINPUT:
                    if self.state == GameState.NAME_INPUT:
                        if len(self.input_name) < 12:
                            self.input_name += event.text

            keys = pygame.key.get_pressed()
            self._update(keys)
            self._draw()
            pygame.display.flip()
            await asyncio.sleep(0)

    # ------------------------------------------------------------------ #
    #  Input                                                               #
    # ------------------------------------------------------------------ #

    def _handle_keydown(self, event) -> bool:
        key = event.key

        if key == pygame.K_ESCAPE:
            return False  # quit

        # --- Start Screen ---
        if self.state == GameState.START:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = GameState.PLAYING
            return True

        # --- Name Input ---
        if self.state == GameState.NAME_INPUT:
            if key == pygame.K_RETURN:
                name = self.input_name.strip() or "Anonym"
                hs.save(name, self.player.points)
                self.state = GameState.START
                self._new_game()
            elif key == pygame.K_BACKSPACE:
                self.input_name = self.input_name[:-1]
            return True

        # --- Neustart ---
        if key == pygame.K_r:
            self.state = GameState.PLAYING
            self._new_game()
            return True

        if self.state != GameState.PLAYING:
            return True

        # --- Spielsteuerung ---
        if key in (pygame.K_UP, pygame.K_w, pygame.K_SPACE):
            self.player.jump()
        if key in (pygame.K_DOWN, pygame.K_s):
            self.player.try_dig("down")
        if key == pygame.K_q:
            self.player.try_dig("left")
        if key == pygame.K_e:
            self.player.try_dig("right")

        return True

    def _update(self, keys):
        if self.state != GameState.PLAYING:
            return

        # Welt horizontal expandieren bevor Spieler sich bewegt
        player_tx = self.player.rect.centerx // C.TILE_SIZE
        self.world.ensure_around(player_tx)

        self.player.update(keys)
        self.camera.update(self.player.rect, self.world)

        # Fluid-Simulation alle 6 Frames
        self._fluid_tick += 1
        if self._fluid_tick >= 6:
            self._fluid_tick = 0
            self.world.tick_fluids()

        if not self.player.alive and self.state == GameState.PLAYING:
            self.state = GameState.GAME_OVER

        if self.player.won and self.state == GameState.PLAYING:
            if hs.is_highscore(self.player.points):
                self.state = GameState.NAME_INPUT
                pygame.key.start_text_input()
            else:
                self.state = GameState.WIN

    # ------------------------------------------------------------------ #
    #  Zeichnen                                                            #
    # ------------------------------------------------------------------ #

    def _draw(self):
        if self.state == GameState.START:
            self.ui.draw_start_screen(self.screen)
            return

        self.screen.fill(C.COLOR_SKY)
        self._draw_world()
        self._draw_player()
        self._draw_hud()

        if self.state == GameState.GAME_OVER:
            self.ui.draw_game_over(self.screen, self.player.points)
        elif self.state == GameState.WIN:
            self.ui.draw_win(self.screen, self.player.points)
        elif self.state == GameState.NAME_INPUT:
            self.ui.draw_name_input(self.screen, self.input_name, self.player.points)

    def _draw_world(self):
        first_row, last_row = self.camera.visible_tile_range()
        first_col, last_col = self.camera.visible_col_range()

        for ty in range(first_row, last_row):
            screen_y = self.camera.world_to_screen_y(ty * C.TILE_SIZE)
            for tx in range(first_col, last_col):
                tile = self.world.get(tx, ty)
                if tile.kind == TileKind.AIR:
                    continue
                screen_x = self.camera.world_to_screen_x(tx * C.TILE_SIZE)
                rect = pygame.Rect(screen_x, screen_y, C.TILE_SIZE, C.TILE_SIZE)
                pygame.draw.rect(self.screen, tile.color, rect)
                pygame.draw.rect(self.screen, (0, 0, 0), rect, 1)

                if tile.kind in (TileKind.RESOURCE, TileKind.DIAMOND):
                    glow = pygame.Surface((C.TILE_SIZE - 6, C.TILE_SIZE - 6), pygame.SRCALPHA)
                    glow.fill((*tile.color[:3], 80))
                    inner = pygame.Rect(
                        screen_x + 3,
                        screen_y + 3,
                        C.TILE_SIZE - 6,
                        C.TILE_SIZE - 6,
                    )
                    self.screen.blit(glow, inner)

    def _draw_player(self):
        screen_rect = self.camera.apply(self.player.rect)
        pygame.draw.rect(self.screen, C.COLOR_PLAYER, screen_rect, border_radius=4)
        eye_y = screen_rect.top + 6
        pygame.draw.circle(self.screen, C.COLOR_BLACK, (screen_rect.left + 6, eye_y), 3)
        pygame.draw.circle(self.screen, C.COLOR_BLACK, (screen_rect.right - 6, eye_y), 3)

    def _draw_hud(self):
        self.ui.draw_hud(self.screen, self.player)
        zone_idx = get_zone_index(self.player.depth() + 2)
        zone_name = C.ZONES[zone_idx]["name"]
        self.ui.draw_zone_name(self.screen, zone_name)

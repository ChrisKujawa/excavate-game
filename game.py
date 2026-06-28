import asyncio
import pygame
import constants as C
from world import World
from player import Player
from camera import Camera
from ui import UI
from tile import TileKind, get_zone_index
from touch_controls import TouchControls
from worm import Worm
import highscore as hs


class _KeysWithTouch:
    """Wraps pygame key state and overlays touch button state."""
    def __init__(self, keys, touch: TouchControls):
        self._keys = keys
        self._touch = touch

    def __getitem__(self, k):
        result = self._keys[k]
        if k in (pygame.K_LEFT, pygame.K_a):
            result = result or self._touch.is_held("left")
        elif k in (pygame.K_RIGHT, pygame.K_d):
            result = result or self._touch.is_held("right")
        return result


class GameState:
    START          = "start"
    PLAYING        = "playing"
    GAME_OVER      = "game_over"
    WIN            = "win"
    LEVEL_COMPLETE = "level_complete"
    NAME_INPUT     = "name_input"


class Game:
    def __init__(self):
        self.screen = pygame.display.get_surface()
        self.clock  = pygame.time.Clock()
        self.ui     = UI()
        self.ui.load_fonts()
        self.touch  = TouchControls()
        self.state  = GameState.START
        self.input_name: str = ""
        self._post_name_state: str = GameState.START
        self.level: int = 1
        self._death_reason: str = "death"  # "death" | "timeout"
        self._new_game()

    def _toggle_fullscreen(self):
        # Explicit depth=32 ensures pygame.draw always gets a supported surface.
        # Without it, set_mode(FULLSCREEN) can return the monitor's native depth
        # (e.g. 30-bit HDR), which pygame.draw rejects and causes a segfault.
        # toggle_fullscreen() is not universally supported by SDL on Linux and
        # can leave the surface in a corrupt state when it fails.
        is_fullscreen = bool(self.screen.get_flags() & pygame.FULLSCREEN)
        if is_fullscreen:
            self.screen = pygame.display.set_mode(
                (C.SCREEN_WIDTH, C.SCREEN_HEIGHT), 0, 32
            )
        else:
            self.screen = pygame.display.set_mode(
                (C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.FULLSCREEN, 32
            )

    def _new_game(self):
        import random
        self.level = 1
        self._death_reason = "death"
        self.world  = World(seed=random.randint(0, 99999), level=self.level)
        self.player = Player(self.world)
        self.camera = Camera()
        self.input_name = ""
        self._fluid_tick = 0
        self.worm: Worm | None = None
        self._init_timer()

    def _new_level(self):
        """Nächstes Level starten – Spieler-Fortschritt bleibt erhalten."""
        import random
        self.level += 1
        old_points   = self.player.points
        old_pickaxe  = self.player.pickaxe_level
        self.world   = World(seed=random.randint(0, 99999), level=self.level)
        self.player  = Player(self.world)
        self.player.points        = old_points
        self.player.pickaxe_level = old_pickaxe
        self.camera  = Camera()
        self._fluid_tick = 0
        self._init_timer()
        # Wurm ab Level 2
        if self.level >= C.WORM_LEVEL_START:
            spawn_ty = self.world.surface_y()
            self.worm = Worm(C.WORLD_WRAP_WIDTH // 2, spawn_ty, self.level)
        else:
            self.worm = None

    def _init_timer(self):
        """Countdown-Timer für das aktuelle Level setzen."""
        idx = min(self.level - 1, len(C.LEVEL_TIME_SECONDS) - 1)
        self.time_left: int = C.LEVEL_TIME_SECONDS[idx] * C.FPS

    # ------------------------------------------------------------------ #
    #  Haupt-Loop                                                          #
    # ------------------------------------------------------------------ #

    async def run(self):
        running = True
        while running:
            self.clock.tick(C.FPS)

            try:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

                    # Any user interaction starts the game from the start screen
                    if self.state == GameState.START and event.type in (
                        pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP,
                        pygame.FINGERDOWN, pygame.FINGERUP,
                    ):
                        self.state = GameState.PLAYING

                    if event.type == pygame.KEYDOWN:
                        running = self._handle_keydown(event)
                    if event.type == pygame.TEXTINPUT:
                        if self.state == GameState.NAME_INPUT:
                            if len(self.input_name) < 12:
                                self.input_name += event.text
                    self.touch.handle_event(event)
                    self._handle_touch_nav(event)

                # One-shot touch actions (jump, dig)
                for action in self.touch.consume_just_pressed():
                    if self.state == GameState.PLAYING:
                        if action == "jump":
                            self.player.jump()
                        elif action == "dig_down":
                            self.player.try_dig("down")
                        elif action == "dig_up":
                            self.player.try_dig("up")

                keys = _KeysWithTouch(pygame.key.get_pressed(), self.touch)
                self._update(keys)
                self._draw()
                pygame.display.flip()
            except Exception as e:
                import traceback
                print("GAME LOOP ERROR:", e)
                traceback.print_exc()
                # Don't kill the loop — keep running so the screen stays visible

            await asyncio.sleep(0)

    # ------------------------------------------------------------------ #
    #  Input                                                               #
    # ------------------------------------------------------------------ #

    def _handle_touch_nav(self, event):
        """Click/tap-to-start and tap-to-restart for pointer input."""
        if event.type not in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            return
        if self.state == GameState.START:
            self.state = GameState.PLAYING
        elif self.state in (GameState.GAME_OVER, GameState.WIN):
            self.state = GameState.PLAYING
            self._new_game()
        elif self.state == GameState.LEVEL_COMPLETE:
            self._start_next_level()

    def _handle_keydown(self, event) -> bool:
        key = event.key

        if key == pygame.K_ESCAPE:
            return False  # quit

        if key == pygame.K_F11:
            self._toggle_fullscreen()
            return True

        # --- Start Screen ---
        if self.state == GameState.START:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = GameState.PLAYING
            return True

        # --- Name Input ---
        if self.state == GameState.NAME_INPUT:
            if key == pygame.K_RETURN:
                name = self.input_name.strip() or "Anonymous"
                hs.save(name, self.player.points)
                pygame.key.stop_text_input()
                self.state = self._post_name_state
            elif key == pygame.K_BACKSPACE:
                self.input_name = self.input_name[:-1]
            return True

        # --- Level Complete ---
        if self.state == GameState.LEVEL_COMPLETE:
            if key in (pygame.K_r, pygame.K_RETURN, pygame.K_SPACE):
                self._start_next_level()
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

    def _start_next_level(self):
        """Zum nächsten Level wechseln oder Sieg-Screen zeigen."""
        if self.level >= C.MAX_LEVELS:
            # Alle Level abgeschlossen → Endsieger
            if hs.is_highscore(self.player.points):
                self._post_name_state = GameState.WIN
                self.state = GameState.NAME_INPUT
                pygame.key.start_text_input()
            else:
                self.state = GameState.WIN
        else:
            self._new_level()
            self.state = GameState.PLAYING

    def _update(self, keys):
        if self.state != GameState.PLAYING:
            return

        # Welt vertikal expandieren (horizontal fest durch Wrapping)
        player_tx = self.player.rect.centerx // C.TILE_SIZE
        player_ty = self.player.rect.bottom  // C.TILE_SIZE
        self.world.ensure_depth(player_ty)

        self.player.update(keys)
        self.camera.update(self.player.rect, self.world)

        # Fluid-Simulation alle 6 Frames
        self._fluid_tick += 1
        if self._fluid_tick >= 6:
            self._fluid_tick = 0
            self.world.tick_fluids()

        # Countdown-Timer
        self.time_left -= 1
        if self.time_left <= 0 and self.state == GameState.PLAYING:
            self._death_reason = "timeout"
            self.player.alive = False

        # Wurm aktualisieren
        player_tx = self.player.rect.centerx // C.TILE_SIZE
        player_ty = self.player.rect.centery // C.TILE_SIZE
        if self.worm is not None and self.player.alive:
            self.worm.update(self.player.trail)
            if self.worm.catches_player(player_tx, player_ty):
                self._death_reason = "death"
                self.player.alive = False

        # Höhlenwürmer aktualisieren (nur innerhalb Erkennungsradius + Puffer)
        if self.player.alive:
            cull = C.CAVE_WORM_DETECT_RADIUS + 5
            for cw in self.world.cave_worms:
                dx = abs(cw.tx - player_tx)
                dx = min(dx, C.WORLD_WRAP_WIDTH - dx)  # wrap-aware
                if dx > cull and abs(cw.ty - player_ty) > cull:
                    continue  # weit entfernt → überspringen
                cw.update(player_tx, player_ty, self.world)
                if cw.catches_player(player_tx, player_ty):
                    self._death_reason = "death"
                    self.player.alive = False
                    break

        if not self.player.alive and self.state == GameState.PLAYING:
            if hs.is_highscore(self.player.points):
                self._post_name_state = GameState.GAME_OVER
                self.state = GameState.NAME_INPUT
                pygame.key.start_text_input()
            else:
                self.state = GameState.GAME_OVER

        if self.player.won and self.state == GameState.PLAYING:
            if self.level >= C.MAX_LEVELS:
                # Letztes Level geschafft → finaler Sieg
                if hs.is_highscore(self.player.points):
                    self._post_name_state = GameState.WIN
                    self.state = GameState.NAME_INPUT
                    pygame.key.start_text_input()
                else:
                    self.state = GameState.WIN
            else:
                self.state = GameState.LEVEL_COMPLETE

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
        if self.worm is not None:
            self.worm.draw(self.screen, self.camera)
        first_row, last_row = self.camera.visible_tile_range()
        first_col, last_col = self.camera.visible_col_range()
        for cw in self.world.cave_worms:
            if first_row <= cw.ty <= last_row and first_col <= cw.tx % C.WORLD_WRAP_WIDTH <= last_col:
                cw.draw(self.screen, self.camera)
        self._draw_hud()
        if C.IS_WEB:
            self.touch.draw(self.screen)

        if self.state == GameState.GAME_OVER:
            self.ui.draw_game_over(self.screen, self.player.points, self._death_reason)
        elif self.state == GameState.WIN:
            self.ui.draw_win(self.screen, self.player.points)
        elif self.state == GameState.LEVEL_COMPLETE:
            self.ui.draw_level_complete(self.screen, self.level, self.player.points)
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
        self.ui.draw_dwarf(self.screen, screen_rect, facing=self.player.facing)
        # Name above player
        name_surf = self.ui.font_small.render(C.PLAYER_NAME, True, C.COLOR_WHITE)
        nx = screen_rect.centerx - name_surf.get_width() // 2
        self.screen.blit(name_surf, (nx, screen_rect.top - name_surf.get_height() - 1))

    def _draw_hud(self):
        self.ui.draw_hud(self.screen, self.player, self.level, self.time_left, self.worm)
        depth = self.player.depth()
        zone_idx = get_zone_index(depth + 2)
        zone_name = C.ZONES[zone_idx]["name"]
        if depth >= C.ZONES[-1]["to"]:
            zone_name = f"{zone_name} (Depth {depth}m)"
        self.ui.draw_zone_name(self.screen, zone_name)

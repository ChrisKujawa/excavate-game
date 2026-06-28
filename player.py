import pygame
import constants as C
from tile import TileKind


class Player:
    def __init__(self, world):
        self.world = world
        # Spawn an der Oberfläche, horizontal zentriert
        # Spawn at world centre (x=0), just above surface
        spawn_ty = world.surface_y()
        self.rect = pygame.Rect(
            (C.TILE_SIZE - C.PLAYER_WIDTH) // 2,   # x=0 centre
            spawn_ty * C.TILE_SIZE - C.PLAYER_HEIGHT,
            C.PLAYER_WIDTH,
            C.PLAYER_HEIGHT,
        )
        self.vel_y: float = 0.0
        self.on_ground: bool = False

        # Spielstatus
        self.hp: int = C.PLAYER_MAX_HP
        self.points: int = 0
        self.pickaxe_level: int = 1
        self.water_timer: int = 0
        self.acid_timer: int = 0
        self.alive: bool = True
        self.won: bool = False

        self.facing: str = "right"

        # Trail für Wurm-Verfolgung
        self.trail: list[tuple[int, int]] = []
        self._last_trail_pos: tuple[int, int] = (-9999, -9999)

        # Feedback-Text (kurz anzeigen)
        self.feedback_text: str = ""
        self.feedback_timer: int = 0

    # ------------------------------------------------------------------ #
    #  Update                                                              #
    # ------------------------------------------------------------------ #

    def update(self, keys):
        if not self.alive:
            return

        self._move_horizontal(keys)
        self._apply_gravity()
        self._move_vertical()
        self._check_tile_effects()
        self._check_upgrades()
        self._record_trail()

        if self.feedback_timer > 0:
            self.feedback_timer -= 1
        else:
            self.feedback_text = ""

    # ------------------------------------------------------------------ #
    #  Graben                                                              #
    # ------------------------------------------------------------------ #

    def try_dig(self, direction: str):
        """
        direction: 'down', 'left', 'right', 'down-left', 'down-right'
        Gibt Punktzahl zurück (0 wenn nicht gegraben).
        """
        tx = self.rect.centerx // C.TILE_SIZE
        ty = self.rect.bottom  // C.TILE_SIZE

        if direction == "down":
            dig_tx, dig_ty = tx, ty
        elif direction == "left":
            dig_tx = (self.rect.left - 1) // C.TILE_SIZE
            dig_ty = self.rect.centery // C.TILE_SIZE
        elif direction == "right":
            dig_tx = self.rect.right // C.TILE_SIZE
            dig_ty = self.rect.centery // C.TILE_SIZE
        else:
            return 0

        tile = self.world.get(dig_tx, dig_ty)

        if tile.kind == TileKind.AIR:
            return 0
        if tile.kind in (TileKind.WATER, TileKind.LAVA, TileKind.ACID):
            return 0
        if tile.hardness > self.pickaxe_level:
            self._show_feedback("Zu hart! (Level " + str(tile.hardness) + " nötig)")
            return 0

        # Gewonnen?
        if tile.kind == TileKind.DIAMOND:
            self.won = True

        earned = tile.points
        self.points += earned
        self.world.remove(dig_tx, dig_ty)

        if earned > 0:
            name = tile.resource_name or "Stein"
            self._show_feedback(f"+{earned} ({name})")

        return earned

    # ------------------------------------------------------------------ #
    #  Bewegung                                                            #
    # ------------------------------------------------------------------ #

    def _move_horizontal(self, keys):
        dx = 0
        if keys[pygame.K_LEFT]  or keys[pygame.K_a]:
            dx = -C.PLAYER_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = C.PLAYER_SPEED

        if dx == 0:
            return

        if dx < 0:
            self.facing = "left"
        else:
            self.facing = "right"

        self.rect.x += dx
        # Kollision mit Wänden → versuche Tile abzubauen
        if self._collides_with_solid(self.rect):
            self.rect.x -= dx
            direction = "left" if dx < 0 else "right"
            self.try_dig(direction)

        # Weltgrenzen (links: nicht vor den generierten Bereich)
        left_limit = self.world.min_tx * C.TILE_SIZE
        self.rect.x = max(left_limit, self.rect.x)

    def _apply_gravity(self):
        self.vel_y += C.GRAVITY
        self.vel_y = min(self.vel_y, C.MAX_FALL_SPEED)

    def _move_vertical(self):
        self.rect.y += int(self.vel_y)
        if self._collides_with_solid(self.rect):
            if self.vel_y > 0:
                # Auf Boden gelandet
                while self._collides_with_solid(self.rect):
                    self.rect.y -= 1
                self.on_ground = True
            else:
                # Kopf gestoßen
                while self._collides_with_solid(self.rect):
                    self.rect.y += 1
            self.vel_y = 0
        else:
            self.on_ground = False

        # Obere Weltgrenze (kein Boden-Limit – Welt ist unendlich tief)
        if self.rect.top < 0:
            self.rect.top = 0
            self.vel_y = 0

    def jump(self):
        if self.on_ground:
            self.vel_y = C.PLAYER_JUMP
            self.on_ground = False

    def _collides_with_solid(self, rect: pygame.Rect) -> bool:
        """Prüft ob rect mit einem soliden Tile kollidiert."""
        left_tx   = rect.left   // C.TILE_SIZE
        right_tx  = (rect.right - 1) // C.TILE_SIZE
        top_ty    = rect.top    // C.TILE_SIZE
        bottom_ty = (rect.bottom - 1) // C.TILE_SIZE

        for ty in range(top_ty, bottom_ty + 1):
            for tx in range(left_tx, right_tx + 1):
                tile = self.world.get(tx, ty)
                if tile.kind in (TileKind.GROUND, TileKind.RESOURCE, TileKind.DIAMOND, TileKind.BEDROCK):
                    return True
        return False

    # ------------------------------------------------------------------ #
    #  Tile-Effekte (Wasser, Lava, Säure)                                 #
    # ------------------------------------------------------------------ #

    def _check_tile_effects(self):
        cx = self.rect.centerx // C.TILE_SIZE
        cy = self.rect.centery // C.TILE_SIZE
        tile = self.world.get(cx, cy)

        if tile.kind == TileKind.LAVA:
            self.hp = 0
            self._die()
        elif tile.kind == TileKind.WATER:
            self.water_timer += 1
            self.acid_timer = 0
            if self.water_timer >= C.WATER_DAMAGE_INTERVAL:
                self.water_timer = 0
                self.hp -= 1
                if self.hp <= 0:
                    self._die()
        elif tile.kind == TileKind.ACID:
            self.acid_timer += 1
            self.water_timer = 0
            if self.acid_timer >= C.ACID_DAMAGE_INTERVAL:
                self.acid_timer = 0
                self.hp -= 1
                if self.hp <= 0:
                    self._die()
        else:
            self.water_timer = 0
            self.acid_timer = 0

    # ------------------------------------------------------------------ #
    #  Upgrades                                                            #
    # ------------------------------------------------------------------ #

    def _check_upgrades(self):
        max_level = len(C.UPGRADE_THRESHOLDS)
        if self.pickaxe_level < max_level:
            threshold = C.UPGRADE_THRESHOLDS[self.pickaxe_level]
            if self.points >= threshold:
                self.pickaxe_level += 1
                self._show_feedback(f">> Spitzhacke Level {self.pickaxe_level}!")

    # ------------------------------------------------------------------ #
    #  Hilfsmethoden                                                       #
    # ------------------------------------------------------------------ #

    def _die(self):
        self.alive = False

    def _show_feedback(self, text: str):
        self.feedback_text = text
        self.feedback_timer = 90  # ~1.5 Sekunden bei 60 FPS

    def _record_trail(self):
        """Aktuelle Tile-Position zum Trail hinzufügen (nur bei Positionsänderung)."""
        tx = self.rect.centerx // C.TILE_SIZE
        ty = self.rect.centery // C.TILE_SIZE
        pos = (tx, ty)
        if pos != self._last_trail_pos:
            self.trail.append(pos)
            self._last_trail_pos = pos
            # Trail auf max. 10000 Einträge begrenzen
            if len(self.trail) > 10000:
                self.trail = self.trail[-10000:]

    def depth(self) -> int:
        """Aktuelle Tiefe in Tiles."""
        return max(0, (self.rect.top // C.TILE_SIZE) - 2)

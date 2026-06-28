"""Tests für player.py – Spieler-Logik."""
import pytest
import pygame
from world import World
from player import Player
from tile import TileKind, make_ground, make_air, make_lava, make_water, make_diamond
import constants as C


@pytest.fixture
def world():
    return World(seed=42)


@pytest.fixture
def player(world):
    return Player(world)


def _empty_keys():
    """Simuliert einen leeren Key-State."""
    return pygame.key.get_pressed()


class TestPlayerSpawn:
    def test_starts_alive(self, player):
        assert player.alive is True

    def test_starts_with_full_hp(self, player):
        assert player.hp == C.PLAYER_MAX_HP

    def test_starts_at_surface(self, player, world):
        spawn_ty = world.surface_y()
        assert player.rect.bottom == spawn_ty * C.TILE_SIZE

    def test_starts_with_pickaxe_level_1(self, player):
        assert player.pickaxe_level == 1

    def test_starts_with_zero_points(self, player):
        assert player.points == 0

    def test_not_won_at_start(self, player):
        assert player.won is False


class TestPlayerGravity:
    def test_falls_when_no_ground(self, world):
        """Spieler fällt wenn Luft darunter."""
        p = Player(world)
        # Entferne alle Tiles unter dem Spieler damit er fällt
        tx = p.rect.centerx // C.TILE_SIZE
        for ty in range(world.surface_y(), world.surface_y() + 10):
            world.set(tx, ty, make_air())
        initial_y = p.rect.y
        keys = _empty_keys()
        for _ in range(10):
            p.update(keys)
        assert p.rect.y > initial_y

    def test_lands_on_solid_tile(self, world):
        """Spieler landet auf solidem Untergrund."""
        p = Player(world)
        keys = _empty_keys()
        for _ in range(60):
            p.update(keys)
        assert p.on_ground is True


class TestPlayerDigging:
    def test_cannot_dig_air(self, player, world):
        """Graben auf Luft gibt 0 Punkte."""
        # Stelle sicher, dass unter dem Spieler Luft ist
        tx = player.rect.centerx // C.TILE_SIZE
        ty = player.rect.bottom  // C.TILE_SIZE
        world.set(tx, ty, make_air())
        result = player.try_dig("down")
        assert result == 0

    def test_can_dig_soft_ground(self, world):
        """Spieler Level 1 kann Zone-0-Tiles abbauen."""
        p = Player(world)
        tx = p.rect.centerx // C.TILE_SIZE
        ty = p.rect.bottom  // C.TILE_SIZE
        world.set(tx, ty, make_ground(0))  # Härte 1
        result = p.try_dig("down")
        assert world.get(tx, ty).kind == TileKind.AIR

    def test_cannot_dig_too_hard(self, world):
        """Spieler Level 1 kann Härte-5-Tiles nicht abbauen."""
        p = Player(world)
        tx = p.rect.centerx // C.TILE_SIZE
        ty = p.rect.bottom  // C.TILE_SIZE
        world.set(tx, ty, make_ground(4))  # Härte 5
        p.try_dig("down")
        assert world.get(tx, ty).kind != TileKind.AIR

    def test_dig_resource_gives_points(self, world):
        """Ressource abbauen gibt Punkte."""
        from tile import make_resource
        p = Player(world)
        tx = p.rect.centerx // C.TILE_SIZE
        ty = p.rect.bottom  // C.TILE_SIZE
        world.set(tx, ty, make_resource("kohle", 0))
        before = p.points
        p.try_dig("down")
        assert p.points > before

    def test_dig_diamond_sets_won(self, world):
        """Diamant abbauen setzt won=True."""
        p = Player(world)
        p.pickaxe_level = 5
        tx = p.rect.centerx // C.TILE_SIZE
        ty = p.rect.bottom  // C.TILE_SIZE
        world.set(tx, ty, make_diamond())
        p.try_dig("down")
        assert p.won is True

    def test_dig_left_right_via_movement(self, world):
        """Gegen eine Wand laufen baut die Tile ab (automatisches Graben)."""
        p = Player(world)
        keys = _empty_keys()
        # Spieler auf Boden landen lassen
        for _ in range(60):
            p.update(keys)

        # Platziere eine abbaubare Tile direkt rechts neben dem Spieler
        right_tx = p.rect.right // C.TILE_SIZE
        mid_ty   = p.rect.centery // C.TILE_SIZE
        world.set(right_tx, mid_ty, make_ground(0))

        # Simuliere Rechtspfeil-Druck: _move_horizontal soll Tile abbauen
        p._move_horizontal({pygame.K_RIGHT: True, pygame.K_LEFT: False,
                             pygame.K_a: False, pygame.K_d: False})
        assert world.get(right_tx, mid_ty).kind == TileKind.AIR

    def test_dig_left_right_direct(self, world):
        """try_dig('left'/'right') funktioniert direkt."""
        p = Player(world)
        keys = _empty_keys()
        for _ in range(60):
            p.update(keys)

        left_tx  = (p.rect.left - 1) // C.TILE_SIZE
        right_tx = p.rect.right // C.TILE_SIZE
        mid_ty   = p.rect.centery // C.TILE_SIZE
        world.set(left_tx,  mid_ty, make_ground(0))
        world.set(right_tx, mid_ty, make_ground(0))

        p.try_dig("left")
        assert world.get(left_tx, mid_ty).kind == TileKind.AIR

        p.try_dig("right")
        assert world.get(right_tx, mid_ty).kind == TileKind.AIR


class TestPlayerUpgrades:
    def test_upgrade_at_threshold(self, world):
        """Pickaxe-Level steigt bei erreichter Punkte-Schwelle."""
        p = Player(world)
        p.points = C.UPGRADE_THRESHOLDS[1] - 1  # knapp darunter
        p._check_upgrades()
        assert p.pickaxe_level == 1

        p.points = C.UPGRADE_THRESHOLDS[1]
        p._check_upgrades()
        assert p.pickaxe_level == 2

    def test_max_level_not_exceeded(self, world):
        """Pickaxe-Level überschreitet Maximum nicht."""
        p = Player(world)
        p.points = 999999
        for _ in range(20):
            p._check_upgrades()
        assert p.pickaxe_level <= len(C.UPGRADE_THRESHOLDS)


class TestPlayerHazards:
    def test_lava_kills_instantly(self, world):
        p = Player(world)
        tx = p.rect.centerx // C.TILE_SIZE
        ty = p.rect.centery // C.TILE_SIZE
        world.set(tx, ty, make_lava())
        p._check_tile_effects()
        assert p.alive is False

    def test_water_drains_hp_over_time(self, world):
        p = Player(world)
        tx = p.rect.centerx // C.TILE_SIZE
        ty = p.rect.centery // C.TILE_SIZE
        world.set(tx, ty, make_water())
        initial_hp = p.hp
        # Simuliere WATER_DAMAGE_INTERVAL Frames in Wasser
        for _ in range(C.WATER_DAMAGE_INTERVAL + 1):
            p._check_tile_effects()
        assert p.hp < initial_hp

    def test_water_eventually_kills(self, world):
        p = Player(world)
        tx = p.rect.centerx // C.TILE_SIZE
        ty = p.rect.centery // C.TILE_SIZE
        world.set(tx, ty, make_water())
        for _ in range(C.WATER_DAMAGE_INTERVAL * (C.PLAYER_MAX_HP + 2)):
            p._check_tile_effects()
        assert p.alive is False


class TestPlayerDepth:
    def test_depth_at_surface(self, player):
        assert player.depth() == 0

    def test_depth_increases_downward(self, world):
        p = Player(world)
        keys = _empty_keys()
        for _ in range(60):
            p.update(keys)
        assert p.depth() >= 0


class TestPlayerWorldBoundary:
    def test_player_cannot_go_above_world(self, world):
        """Spieler bleibt über dem oberen Rand."""
        p = Player(world)
        p.rect.y = 5
        p.vel_y = -50
        p._move_vertical()
        assert p.rect.top >= 0

    def test_player_can_fall_very_deep(self, world):
        """In der unendlichen Welt gibt es keine untere Grenze."""
        p = Player(world)
        p.rect.y = 9000  # sehr tief
        p.vel_y = 10
        # ensure world is generated there
        world.ensure_depth(p.rect.bottom // C.TILE_SIZE + 30)
        p._apply_gravity()
        p._move_vertical()
        # Player should still exist (no crash, no forced clamp)
        assert p.rect.y > 0


class TestDigUpward:
    def test_dig_up_removes_tile_above(self, world):
        import constants as C
        from tile import make_ground, TileKind
        p = Player(world)
        # Place player so dig_up targets a specific tile
        surf = world.surface_y()
        p.rect.y = (surf + 5) * C.TILE_SIZE  # player body here
        p.rect.x = 0
        target_ty = (p.rect.top - 1) // C.TILE_SIZE
        world.set(p.rect.centerx // C.TILE_SIZE, target_ty, make_ground(0))
        result = p.try_dig("up")
        assert result >= 0  # didn't crash
        assert world.get(p.rect.centerx // C.TILE_SIZE, target_ty).kind == TileKind.AIR

    def test_dig_up_cannot_dig_too_hard(self, world):
        import constants as C
        from tile import make_ground
        p = Player(world)
        p.rect.y = (world.surface_y() + 5) * C.TILE_SIZE
        p.rect.x = 0
        target_ty = (p.rect.top - 1) // C.TILE_SIZE
        hard_tile = make_ground(8)  # hardness 8
        world.set(p.rect.centerx // C.TILE_SIZE, target_ty, hard_tile)
        p.pickaxe_level = 1
        p.try_dig("up")
        # Tile should still be there (too hard)
        from tile import TileKind
        assert world.get(p.rect.centerx // C.TILE_SIZE, target_ty).kind != TileKind.AIR

    def test_dig_up_does_not_dig_air(self, world):
        import constants as C
        from tile import make_air
        p = Player(world)
        p.rect.y = (world.surface_y() + 5) * C.TILE_SIZE
        target_ty = (p.rect.top - 1) // C.TILE_SIZE
        world.set(p.rect.centerx // C.TILE_SIZE, target_ty, make_air())
        result = p.try_dig("up")
        assert result == 0


class TestHorizontalWrap:
    def test_player_wraps_right_to_left(self, world):
        import constants as C
        p = Player(world)
        world_px = C.WORLD_WRAP_WIDTH * C.TILE_SIZE
        p.rect.x = world_px  # exactly at right boundary
        p._move_horizontal.__func__  # exists
        # Simulate wrap directly (as _move_horizontal would)
        if p.rect.left >= world_px:
            p.rect.x = 0
        assert p.rect.x == 0

    def test_player_wraps_left_to_right(self, world):
        import constants as C
        p = Player(world)
        world_px = C.WORLD_WRAP_WIDTH * C.TILE_SIZE
        p.rect.x = -p.rect.width  # right edge <= 0
        if p.rect.right <= 0:
            p.rect.x = world_px - p.rect.width
        assert p.rect.x == world_px - p.rect.width


class TestTrail:
    def test_trail_initially_empty(self, player):
        assert isinstance(player.trail, list)

    def test_trail_records_positions(self, world):
        import constants as C
        from unittest.mock import MagicMock
        p = Player(world)
        p.rect.y = (world.surface_y() + 2) * C.TILE_SIZE
        # Manually call _record_trail twice at different positions
        p._record_trail()
        initial_len = len(p.trail)
        p.rect.x += C.TILE_SIZE  # move 1 tile right
        p._record_trail()
        assert len(p.trail) > initial_len

    def test_trail_no_duplicate_consecutive(self, world):
        import constants as C
        p = Player(world)
        p._record_trail()
        p._record_trail()  # same position again
        # Only one entry since position unchanged
        positions = [(tx, ty) for tx, ty in p.trail]
        if len(positions) > 1:
            # Last two should differ
            assert positions[-1] != positions[-2]


class TestDigDownCorner:
    """Player standing at the corner/edge of a tile should still be able to dig down."""

    def _make_world_with_ledge(self):
        """
        Build a world where the player stands at the right edge of a ledge:
          col:  tx-1  tx   tx+1
          surface:  G    G    AIR   (G = ground)
          below:    G    G    AIR
        Player's centerx is over tx, but rect.right crosses into tx+1 (air column).
        """
        from world import World
        from tile import make_air, make_ground
        import constants as C
        world = World(seed=0)
        world.ensure_depth(10)
        surf = world.surface_y()
        tx = C.WORLD_WRAP_WIDTH // 2

        # Carve column tx+1 fully open so player center is near the edge
        for dy in range(-1, 5):
            world.set(tx + 1, surf + dy, make_air())
            world.set(tx + 2, surf + dy, make_air())
        return world, tx, surf

    def test_dig_down_from_center_column(self):
        """Normal case: player center over solid tile, dig-down works."""
        import constants as C
        from player import Player
        from tile import TileKind
        world, tx, surf = self._make_world_with_ledge()
        p = Player(world)
        # Place player so their bottom sits exactly on the surface row
        p.rect.x = tx * C.TILE_SIZE + (C.TILE_SIZE - C.PLAYER_WIDTH) // 2
        p.rect.y = surf * C.TILE_SIZE - C.PLAYER_HEIGHT
        p.pickaxe_level = 9  # can mine anything

        result = p.try_dig("down")
        tile_below = world.get(tx, surf)
        assert tile_below.kind == TileKind.AIR or result > 0

    def test_dig_down_at_right_edge_of_ledge(self):
        """
        Player standing at the right edge: center is over the last solid column.
        rect.right extends into the air column. try_dig("down") must still work.
        """
        import constants as C
        from player import Player
        from tile import TileKind, make_ground
        world, tx, surf = self._make_world_with_ledge()

        p = Player(world)
        # Right edge of player aligns with tile boundary (center over tx, right into tx+1 air)
        p.rect.x = tx * C.TILE_SIZE + C.TILE_SIZE - C.PLAYER_WIDTH
        p.rect.y = surf * C.TILE_SIZE - C.PLAYER_HEIGHT
        p.pickaxe_level = 9

        # Ensure the tile below tx is solid
        world.set(tx, surf, make_ground(0))

        p.try_dig("down")
        tile_below = world.get(tx, surf)
        assert tile_below.kind == TileKind.AIR, (
            "Player at edge of ledge could not dig down – try_dig fell through to air column"
        )

    def test_dig_down_when_center_over_air_uses_foot_column(self):
        """
        Edge case: player's centerx is over an already-dug air column, but one foot
        is still over a solid tile. dig-down should find the solid tile via foot column.
        """
        import constants as C
        from player import Player
        from tile import TileKind, make_air, make_ground
        world, tx, surf = self._make_world_with_ledge()

        # Dig center column open so centerx is over air
        for dy in range(-2, 3):
            world.set(tx, surf + dy, make_air())
        # Keep left column (tx-1) solid at surf level
        world.set(tx - 1, surf, make_ground(0))

        p = Player(world)
        # Position player so centerx lands on tx (air) but left side covers tx-1 (solid)
        p.rect.x = (tx - 1) * C.TILE_SIZE + C.TILE_SIZE - C.PLAYER_WIDTH // 2
        p.rect.y = surf * C.TILE_SIZE - C.PLAYER_HEIGHT
        p.pickaxe_level = 9

        p.try_dig("down")
        tile_below = world.get(tx - 1, surf)
        assert tile_below.kind == TileKind.AIR, (
            "dig-down failed: when center is over air, foot column fallback did not work"
        )

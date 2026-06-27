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
    def test_player_cannot_fall_below_world(self, world):
        """Spieler bleibt innerhalb der Weltgrenzen."""
        p = Player(world)
        # Teleportiere Spieler fast ans untere Ende
        p.rect.y = C.WORLD_HEIGHT * C.TILE_SIZE - C.PLAYER_HEIGHT - 5
        p.vel_y = 50  # hohe Fallgeschwindigkeit
        keys = _empty_keys()
        for _ in range(10):
            p._apply_gravity()
            p._move_vertical()
        assert p.rect.bottom <= C.WORLD_HEIGHT * C.TILE_SIZE

    def test_player_cannot_go_above_world(self, world):
        """Spieler bleibt über dem oberen Rand."""
        p = Player(world)
        p.rect.y = 5
        p.vel_y = -50
        p._move_vertical()
        assert p.rect.top >= 0

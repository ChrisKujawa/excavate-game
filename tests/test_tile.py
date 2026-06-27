"""Tests für tile.py – Tile-Typen und Fabrik-Funktionen."""
import pytest
from tile import (
    TileKind,
    make_air, make_ground, make_resource, make_water, make_lava,
    make_diamond, get_zone_index,
)
import constants as C


class TestMakeAir:
    def test_kind(self):
        assert make_air().kind == TileKind.AIR

    def test_hardness_zero(self):
        assert make_air().hardness == 0

    def test_no_resource(self):
        assert make_air().resource_name is None


class TestMakeGround:
    def test_kind(self):
        for i in range(len(C.ZONES)):
            assert make_ground(i).kind == TileKind.GROUND

    def test_hardness_matches_zone(self):
        for i, zone in enumerate(C.ZONES):
            assert make_ground(i).hardness == zone["hardness"]

    def test_color_matches_zone(self):
        for i, zone in enumerate(C.ZONES):
            assert make_ground(i).color == zone["color"]


class TestMakeResource:
    def test_kind(self):
        assert make_resource("kohle", 1).kind == TileKind.RESOURCE

    def test_points(self):
        assert make_resource("kohle", 1).points == C.RESOURCES["kohle"]["points"]
        assert make_resource("saphir", 4).points == C.RESOURCES["saphir"]["points"]

    def test_resource_name_stored(self):
        tile = make_resource("eisen", 2)
        assert tile.resource_name == "eisen"

    def test_hardness_from_zone(self):
        tile = make_resource("kohle", 1)
        assert tile.hardness == C.ZONES[1]["hardness"]


class TestMakeWaterLava:
    def test_water_kind(self):
        assert make_water().kind == TileKind.WATER

    def test_lava_kind(self):
        assert make_lava().kind == TileKind.LAVA

    def test_water_not_solid(self):
        assert make_water().hardness == 0

    def test_lava_not_solid(self):
        assert make_lava().hardness == 0


class TestMakeDiamond:
    def test_kind(self):
        assert make_diamond().kind == TileKind.DIAMOND

    def test_max_hardness(self):
        assert make_diamond().hardness == 5

    def test_high_points(self):
        assert make_diamond().points >= 9999


class TestGetZoneIndex:
    def test_surface_zone(self):
        assert get_zone_index(0) == 0
        assert get_zone_index(5) == 0

    def test_zone_boundaries(self):
        for i, zone in enumerate(C.ZONES):
            assert get_zone_index(zone["from"]) == i

    def test_last_zone_for_deep(self):
        assert get_zone_index(C.WORLD_HEIGHT - 1) == len(C.ZONES) - 1

    def test_beyond_world_clamps(self):
        result = get_zone_index(9999)
        assert result == len(C.ZONES) - 1

from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional
import constants as C


class TileKind(Enum):
    AIR      = auto()
    GROUND   = auto()   # abbaubares Erdreich/Stein
    RESOURCE = auto()   # Ressource (Kohle, Eisen, etc.)
    WATER    = auto()
    LAVA     = auto()
    DIAMOND  = auto()   # Riesiger Diamant – Win-Tile
    BEDROCK  = auto()   # Unzerstörbarer Boden


@dataclass
class Tile:
    kind: TileKind
    hardness: int = 0          # wie viele Pickaxe-Level nötig
    color: tuple = (0, 0, 0)
    resource_name: Optional[str] = None   # z.B. "kohle"
    points: int = 0


# --- Fabrik-Funktionen ---

def make_air() -> Tile:
    return Tile(kind=TileKind.AIR, hardness=0, color=C.COLOR_SKY)


def make_ground(zone_index: int) -> Tile:
    z = C.ZONES[zone_index]
    return Tile(kind=TileKind.GROUND, hardness=z["hardness"], color=z["color"])


def make_resource(resource_name: str, zone_index: int) -> Tile:
    res = C.RESOURCES[resource_name]
    z = C.ZONES[zone_index]
    return Tile(
        kind=TileKind.RESOURCE,
        hardness=z["hardness"],
        color=res["color"],
        resource_name=resource_name,
        points=res["points"],
    )


def make_water() -> Tile:
    return Tile(kind=TileKind.WATER, hardness=0, color=C.COLOR_WATER)


def make_lava() -> Tile:
    return Tile(kind=TileKind.LAVA, hardness=0, color=C.COLOR_LAVA)


def make_diamond() -> Tile:
    return Tile(
        kind=TileKind.DIAMOND,
        hardness=5,
        color=(185, 242, 255),
        resource_name="diamant",
        points=9999,
    )


def make_bedrock() -> Tile:
    return Tile(kind=TileKind.BEDROCK, hardness=99, color=(15, 10, 15))


def get_zone_index(tile_y: int) -> int:
    """Gibt den Zonen-Index für eine Tile-Y-Position zurück."""
    for i, z in enumerate(C.ZONES):
        if z["from"] <= tile_y < z["to"]:
            return i
    return len(C.ZONES) - 1

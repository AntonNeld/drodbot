from enum import Enum

from pydantic import BaseModel


class ElementType(Enum):
    """A kind of game element."""

    UNKNOWN = "Unknown"
    NOTHING = "Nothing"
    WALL = "Wall"
    PIT = "Pit"
    MASTER_WALL = "Master wall"
    YELLOW_DOOR = "Yellow door"
    YELLOW_DOOR_OPEN = "Yellow door (open)"
    GREEN_DOOR = "Green door"
    GREEN_DOOR_OPEN = "Green door (open)"
    BLUE_DOOR = "Blue door"
    BLUE_DOOR_OPEN = "Blue door (open)"
    STAIRS = "Stairs"
    FORCE_ARROW = "Force arrow"
    CHECKPOINT = "Checkpoint"
    ORB = "Orb"
    SCROLL = "Scroll"
    OBSTACLE = "Obstacle"
    BEETHRO = "Beethro"
    BEETHRO_SWORD = "Really Big Sword (TM)"
    ROACH = "Roach"
    CONQUER_TOKEN = "Conquer token"
    FLOOR = "Floor"


# Which elements can be in which layers
ROOM_PIECES = [
    ElementType.WALL,
    ElementType.FLOOR,
    ElementType.PIT,
    ElementType.MASTER_WALL,
    ElementType.YELLOW_DOOR,
    ElementType.YELLOW_DOOR_OPEN,
    ElementType.GREEN_DOOR,
    ElementType.GREEN_DOOR_OPEN,
    ElementType.BLUE_DOOR,
    ElementType.BLUE_DOOR_OPEN,
    ElementType.STAIRS,
]
FLOOR_CONTROLS = [ElementType.FORCE_ARROW, ElementType.NOTHING]
CHECKPOINTS = [ElementType.CHECKPOINT, ElementType.NOTHING]
ITEMS = [
    ElementType.CONQUER_TOKEN,
    ElementType.ORB,
    ElementType.SCROLL,
    ElementType.OBSTACLE,
    ElementType.NOTHING,
]
MONSTERS = [
    ElementType.BEETHRO,
    ElementType.ROACH,
    ElementType.NOTHING,
]


class Direction(Enum):
    """A direction of an element.

    Not all elements can have all directions, but this is not enforced.
    """

    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"
    NONE = " "
    UNKNOWN = "?"


class Element(BaseModel):
    """An game element that can be in a tile."""

    element_type: ElementType
    direction: Direction


def element_from_apparent(element_type, direction):
    """Create an element from an element type and a direction.

    Some information may be missing initially.

    Parameters
    ----------
    element_type
        The element type.
    direction
        The direction.
    """
    return Element(element_type=element_type, direction=direction)

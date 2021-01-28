from enum import Enum
from typing import Union, Literal, List, Tuple

from pydantic import BaseModel


class ElementType(str, Enum):
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


class Direction(str, Enum):
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


class UndirectionalElement(BaseModel):
    """An game element without a direction."""

    element_type: Union[
        Literal[ElementType.UNKNOWN],
        Literal[ElementType.WALL],
        Literal[ElementType.FLOOR],
        Literal[ElementType.PIT],
        Literal[ElementType.MASTER_WALL],
        Literal[ElementType.YELLOW_DOOR],
        Literal[ElementType.YELLOW_DOOR_OPEN],
        Literal[ElementType.GREEN_DOOR],
        Literal[ElementType.GREEN_DOOR_OPEN],
        Literal[ElementType.BLUE_DOOR],
        Literal[ElementType.BLUE_DOOR_OPEN],
        Literal[ElementType.STAIRS],
        Literal[ElementType.CHECKPOINT],
        Literal[ElementType.CONQUER_TOKEN],
        Literal[ElementType.SCROLL],
        Literal[ElementType.OBSTACLE],
    ]


class OrbEffectType(str, Enum):
    TOGGLE = "toggle"
    OPEN = "open"
    CLOSE = "close"


class Orb(BaseModel):
    element_type: Literal[ElementType.ORB] = ElementType.ORB
    effects: List[Tuple[OrbEffectType, Tuple[int, int]]] = []


class DirectionalElement(BaseModel):
    """An game element with a direction."""

    element_type: Union[Literal[ElementType.FORCE_ARROW], Literal[ElementType.ROACH]]
    direction: Direction


# Let's make Beethro a separate class because we instantiate him so often
class Beethro(BaseModel):
    """The player."""

    element_type: Literal[ElementType.BEETHRO] = ElementType.BEETHRO
    direction: Direction


Element = Union[UndirectionalElement, Orb, DirectionalElement, Beethro]


def element_from_apparent(element_type, direction, orb_effects=None):
    """Create an element from an element type and a direction.

    Some information may be missing initially. ElementType.NOTHING becomes None.

    Parameters
    ----------
    element_type
        The element type.
    direction
        The direction.

    Returns
    -------
    An element or None.
    """
    if element_type == ElementType.NOTHING:
        return None
    if element_type == ElementType.BEETHRO:
        return Beethro(direction=direction)
    if element_type == ElementType.ORB:
        return Orb(effects=orb_effects) if orb_effects is not None else Orb()
    if direction == Direction.NONE:
        return UndirectionalElement(element_type=element_type)
    return DirectionalElement(element_type=element_type, direction=direction)

from enum import Enum


class Element(Enum):
    """A game element that can be in a tile."""

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
    Element.WALL,
    Element.FLOOR,
    Element.PIT,
    Element.MASTER_WALL,
    Element.YELLOW_DOOR,
    Element.YELLOW_DOOR_OPEN,
    Element.GREEN_DOOR,
    Element.GREEN_DOOR_OPEN,
    Element.BLUE_DOOR,
    Element.BLUE_DOOR_OPEN,
    Element.STAIRS,
]
FLOOR_CONTROLS = [Element.FORCE_ARROW, Element.NOTHING]
CHECKPOINTS = [Element.CHECKPOINT, Element.NOTHING]
ITEMS = [
    Element.CONQUER_TOKEN,
    Element.ORB,
    Element.SCROLL,
    Element.OBSTACLE,
    Element.NOTHING,
]
MONSTERS = [Element.BEETHRO, Element.ROACH, Element.NOTHING]


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

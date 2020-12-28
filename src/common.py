from dataclasses import dataclass
from enum import Enum
from typing import Tuple, Optional, List


class UserError(Exception):
    pass


class Action(Enum):
    N = 8
    NE = 9
    E = 6
    SE = 3
    S = 2
    SW = 1
    W = 4
    NW = 7
    WAIT = 5
    CW = 10
    CCW = 11


class GUIEvent(Enum):
    QUIT = "quit"
    DISPLAY_IMAGE = "display_image"


# The values are also what will be displayed in the GUI
class ImageProcessingStep(Enum):
    SCREENSHOT = "Screenshot"
    FIND_UPPER_EDGE_COLOR = "Find upper edge color"
    FIND_UPPER_EDGE_LINE = "Find upper edge line"
    CROP_WINDOW = "Extract DROD window"
    CROP_ROOM = "Extract room"
    EXTRACT_TILES = "Extract tiles"
    AVERAGE_TILE_COLOR = "Average tile color"
    CLASSIFY_TILES = "Classify tiles"


# The values are also what will be displayed in the GUI
class Strategy(Enum):
    MOVE_TO_CONQUER_TOKEN = "Move to a conquer token"
    MOVE_RANDOMLY = "30 random moves"


# The values are also what will be displayed with "Get view"
class Element(Enum):
    UNKNOWN = "?"
    WALL = "#"
    BEETHRO = "B"
    CONQUER_TOKEN = "V"
    TRIGGERED_CONQUER_TOKEN = "v"
    FLOOR = "."


class Direction(Enum):
    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"
    NONE = "N/A"
    UNKNOWN = "?"


@dataclass
class Tile:
    """A representation of a tile.

    This contains information about what element is in each layer, as a tuple of
    (Element, Direction). If a layer has nothing in it, the value is None.

    Parameters
    ----------
    room_piece
        The element in the "room pieces" layer. This cannot be None.
    floor_control
        The element in the "floor controls" layer (excluding checkpoints and lighting).
    checkpoint
        The element in the checkpoints layer.
    item
        The element in the "items" layer.
    monster
        The element in the "monsters" layer.
    swords
        A list of elements in the swords layer.
    """

    room_piece: Tuple[Element, Direction]
    floor_control: Optional[Tuple[Element, Direction]] = None
    checkpoint: Optional[Tuple[Element, Direction]] = None
    item: Optional[Tuple[Element, Direction]] = None
    monster: Optional[Tuple[Element, Direction]] = None
    swords: Optional[List[Tuple[Element, Direction]]] = None

    def get_elements(self):
        """Get all elements in the tile.

        Returns
        -------
        A list of all elements (without directions) in the tile.
        """
        elements = []
        for element in [
            self.room_piece,
            self.floor_control,
            self.checkpoint,
            self.item,
            self.monster,
        ] + (self.swords if self.swords is not None else []):
            if element is not None:
                elements.append(element[0])
        return elements


class Room:
    """A representation of a room."""

    def __init__(self):
        self._tiles = {}

    def set_tile(self, position, tile):
        """Set the contents of a tile.

        Parameters
        ----------
        position
            The coordinates of the tile, given as a tuple (x, y).
        elements
            A Tile instance containing the elements of the tile.
        """
        self._tiles[position] = tile

    def find_coordinates(self, element):
        """Find the coordinates of all elements of a type.

        Parameters
        ----------
        element
            The element to find the coordinates of.

        Returns
        -------
        The coordinates of all elements of that type, as a list of (x, y) tuples.
        """
        return [
            pos for pos, tile in self._tiles.items() if element in tile.get_elements()
        ]

    def find_player(self):
        """Find the coordinates of the player.

        Returns
        -------
        The coordinates of the player, as an (x, y) tuple.
        """
        beethros = self.find_coordinates(Element.BEETHRO)
        if len(beethros) < 1:
            raise RuntimeError("Cannot find Beethro")
        if len(beethros) > 1:
            raise RuntimeError(f"Too many Beethros: {beethros}")
        return beethros[0]

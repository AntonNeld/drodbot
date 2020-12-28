from enum import Enum


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


class Room:
    """A representation of a room."""

    def __init__(self):
        self._tiles = {}

    def set_tile(self, position, elements):
        """Set the contents of a tile.

        Parameters
        ----------
        position
            The coordinates of the tile, given as a tuple (x, y).
        elements
            The elements to put in the tile.
        """
        self._tiles[position] = elements

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
        return [pos for pos, entities in self._tiles.items() if element in entities]

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

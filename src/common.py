import copy
from dataclasses import dataclass
from enum import Enum
import json
from typing import Tuple


ROOM_WIDTH_IN_TILES = 38
ROOM_HEIGHT_IN_TILES = 32
TILE_SIZE = 22


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
    SET_INTERPRET_SCREEN_DATA = "set_interpret_screen_data"
    SET_TRAINING_DATA = "set_training_data"


# The values are also what will be displayed in the GUI
class ImageProcessingStep(Enum):
    SCREENSHOT = "Screenshot"
    FIND_UPPER_EDGE_COLOR = "Find upper edge color"
    FIND_UPPER_EDGE_LINE = "Find upper edge line"
    CROP_WINDOW = "Extract DROD window"
    CROP_ROOM = "Extract room"
    EXTRACT_TILES = "Extract tiles"
    EXTRACT_MINIMAP = "Extract minimap"
    CLASSIFY_TILES = "Classify tiles"


# The values are also what will be displayed in the GUI
class Strategy(Enum):
    MOVE_TO_CONQUER_TOKEN = "Move to a conquer token"
    MOVE_RANDOMLY = "30 random moves"


class Element(Enum):
    UNKNOWN = "Unknown"
    NOTHING = "Nothing"
    WALL = "Wall"
    PIT = "Pit"
    MASTER_WALL = "Master wall"
    YELLOW_DOOR = "Yellow door"
    YELLOW_DOOR_OPEN = "Yellow door (open)"
    STAIRS = "Stairs"
    OBSTACLE = "Obstacle"
    BEETHRO = "Beethro"
    CONQUER_TOKEN = "Conquer token"
    FLOOR = "Floor"


ROOM_PIECES = [
    Element.WALL,
    Element.FLOOR,
    Element.PIT,
    Element.MASTER_WALL,
    Element.YELLOW_DOOR,
    Element.YELLOW_DOOR_OPEN,
    Element.STAIRS,
]
ITEMS = [Element.CONQUER_TOKEN, Element.OBSTACLE, Element.NOTHING]
MONSTERS = [Element.BEETHRO, Element.NOTHING]

# These are overlaid over the room to show tile classifications
ELEMENT_CHARACTERS = {
    Element.UNKNOWN: "?",
    Element.WALL: "#",
    Element.PIT: ",",
    Element.MASTER_WALL: "M",
    Element.YELLOW_DOOR: "Y",
    Element.YELLOW_DOOR_OPEN: "y",
    Element.STAIRS: ">",
    Element.OBSTACLE: "+",
    Element.BEETHRO: "B",
    Element.CONQUER_TOKEN: "C",
    Element.FLOOR: ".",
}


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


ALLOWED_DIRECTIONS = {
    **{e: [Direction.NONE] for e in (ROOM_PIECES + ITEMS)},
    **{
        e: [
            Direction.N,
            Direction.NE,
            Direction.E,
            Direction.SE,
            Direction.S,
            Direction.SW,
            Direction.W,
            Direction.NW,
        ]
        for e in MONSTERS
    },
    Element.NOTHING: [Direction.NONE],  # Overwrites any earlier Nothings
}


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
    """

    room_piece: Tuple[Element, Direction]
    floor_control: Tuple[Element, Direction] = (Element.NOTHING, Direction.NONE)
    checkpoint: Tuple[Element, Direction] = (Element.NOTHING, Direction.NONE)
    item: Tuple[Element, Direction] = (Element.NOTHING, Direction.NONE)
    monster: Tuple[Element, Direction] = (Element.NOTHING, Direction.NONE)

    def get_elements(self):
        """Get all elements in the tile.

        Element.NOTHING is skipped.

        Returns
        -------
        A list of all elements (without directions) in the tile.
        """
        return [
            e[0]
            for e in [
                self.room_piece,
                self.floor_control,
                self.checkpoint,
                self.item,
                self.monster,
            ]
            if e[0] != Element.NOTHING
        ]

    def to_json(self):
        """Encodes the tile as JSON.

        Returns
        -------
        The JSON-encoded tile.
        """

        return json.dumps(
            {
                "room_piece": [e.value for e in self.room_piece],
                "floor_control": [e.value for e in self.floor_control],
                "checkpoint": [e.value for e in self.checkpoint],
                "item": [e.value for e in self.item],
                "monster": [e.value for e in self.monster],
            }
        )

    @staticmethod
    def from_json(json_string):
        json_dict = json.loads(json_string)
        constructor_args = {
            key: _element_tuple_from_json(value) for key, value in json_dict.items()
        }
        return Tile(**constructor_args)


def _element_tuple_from_json(pair):
    element = next(e for e in Element if e.value == pair[0])
    direction = next(d for d in Direction if d.value == pair[1])
    return (element, direction)


class Room:
    """A representation of a room."""

    def __init__(self):
        self._tiles = {}
        # Since this class is used when generating training data, and
        # we don't want to use classification then, initialize the room
        # as empty.
        for x in range(ROOM_WIDTH_IN_TILES):
            for y in range(ROOM_HEIGHT_IN_TILES):
                self._tiles[(x, y)] = Tile(room_piece=(Element.FLOOR, Direction.NONE))

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

    def get_tile(self, position):
        """Get the contents of a tile.

        Parameters
        ----------
        position
            The coordinates of the tile, given as a tuple (x, y).

        Returns
        -------
        The Tile object for the given position.
        """
        return self._tiles[position]

    def place_element_like_editor(
        self, element, direction, position, end_position=None
    ):
        """Place an element, like in the editor.

        If an element already exists in the square, and it would block
        the new element from being placed, the element is not placed.

        Parameters
        ----------
        element
            The element to place.
        direction
            The direction the element is facing. Use Direction.NONE if not applicable.
        position
            The position to place the element as a tuple (x, y). If `end_position`
            is not None, this is the upper left corner of the square.
        end_position
            If this is not None, place elements in a square with this as the lower
            right corner.
        """
        if element in ROOM_PIECES:
            layer = "room_piece"
        elif element in ITEMS:
            layer = "item"
        elif element in MONSTERS:
            layer = "monster"
        else:
            raise RuntimeError(f"Element {element} not in any layer")
        for x in range(
            position[0],
            end_position[0] + 1 if end_position is not None else position[0] + 1,
        ):
            for y in range(
                position[1],
                end_position[1] + 1 if end_position is not None else position[1] + 1,
            ):
                tile = copy.deepcopy(self._tiles[(x, y)])
                # Cannot place things on same layer as something else, unless it's
                # a floor.
                if getattr(tile, layer)[0] not in [Element.FLOOR, Element.NOTHING]:
                    continue
                # TODO: There are some elements that block each other, even if they are
                #       on different layers. Once we use enough elements that it is
                #       relevant, take care of this here.
                setattr(tile, layer, (element, direction))
                self._tiles[(x, y)] = tile

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

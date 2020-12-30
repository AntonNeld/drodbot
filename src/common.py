import copy
from dataclasses import dataclass, field
from enum import Enum
import json
from typing import Tuple, Optional, List


ROOM_WIDTH_IN_TILES = 38
ROOM_HEIGHT_IN_TILES = 32


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
    TRAINING_DATA = "training_data"


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
    BEETHRO_SWORD = "S"
    CONQUER_TOKEN = "V"
    TRIGGERED_CONQUER_TOKEN = "v"
    FLOOR = "."


ROOM_PIECES = [Element.WALL, Element.FLOOR]
ITEMS = [Element.CONQUER_TOKEN, Element.TRIGGERED_CONQUER_TOKEN]
MONSTERS = [Element.BEETHRO]
SWORDS = [Element.BEETHRO_SWORD]

SWORDED_MONSTERS = {Element.BEETHRO: Element.BEETHRO_SWORD}


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
    swords: List[Tuple[Element, Direction]] = field(default_factory=list)

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
        ] + self.swords:
            if element is not None:
                elements.append(element[0])
        return elements

    def to_json(self):
        """Encodes the tile as JSON.

        Returns
        -------
        The JSON-encoded tile.
        """

        return json.dumps(
            {
                "room_piece": [e.value for e in self.room_piece],
                "floor_control": [e.value for e in self.floor_control]
                if self.floor_control is not None
                else None,
                "checkpoint": [e.value for e in self.checkpoint]
                if self.checkpoint is not None
                else None,
                "item": [e.value for e in self.item] if self.item is not None else None,
                "monster": [e.value for e in self.monster]
                if self.monster is not None
                else None,
                "swords": [[e.value for e in element] for element in self.swords],
            }
        )

    @staticmethod
    def from_json(json_string):
        json_dict = json.loads(json_string)
        constructor_args = {
            key: _element_tuple_from_json(value)
            for key, value in json_dict.items()
            if key != "swords"
        }
        constructor_args["swords"] = [
            _element_tuple_from_json(p) for p in json_dict["swords"]
        ]
        return Tile(**constructor_args)


def _element_tuple_from_json(pair):
    if pair is None:
        return None
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
                # Cannot place things on same layer as something else. We don't need to
                # worry about swords, since they can't be placed individually.
                if getattr(tile, layer) is not None:
                    continue
                # TODO: There are some elements that block each other, even if they are
                #       on different layers. Once we use enough elements that it is
                #       relevant, take care of this here.
                setattr(tile, layer, (element, direction))
                self._tiles[(x, y)] = tile
                if element in SWORDED_MONSTERS:
                    sword = SWORDED_MONSTERS[element]
                    if direction == Direction.N:
                        sword_pos = (x, y - 1)
                    elif direction == Direction.NE:
                        sword_pos = (x + 1, y - 1)
                    elif direction == Direction.E:
                        sword_pos = (x + 1, y)
                    elif direction == Direction.SE:
                        sword_pos = (x + 1, y + 1)
                    elif direction == Direction.S:
                        sword_pos = (x, y + 1)
                    elif direction == Direction.SW:
                        sword_pos = (x - 1, y + 1)
                    elif direction == Direction.W:
                        sword_pos = (x - 1, y)
                    elif direction == Direction.NW:
                        sword_pos = (x - 1, y - 1)
                    else:
                        raise RuntimeError(f"Sword cannot have direction {direction}")
                    try:
                        sword_tile = copy.deepcopy(self._tiles[sword_pos])
                        sword_tile.swords.append((sword, direction))
                    except KeyError:
                        pass  # Don't place a sword outside the room

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

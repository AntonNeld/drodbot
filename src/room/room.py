import copy
from pydantic import BaseModel, Field
from typing import Dict, Tuple

from common import ROOM_WIDTH_IN_TILES, ROOM_HEIGHT_IN_TILES
from .element import (
    Element,
    Direction,
    ROOM_PIECES,
    FLOOR_CONTROLS,
    CHECKPOINTS,
    ITEMS,
    MONSTERS,
)
from .tile import Tile


def _create_empty_room():
    tiles = {}
    for x in range(ROOM_WIDTH_IN_TILES):
        for y in range(ROOM_HEIGHT_IN_TILES):
            tiles[(x, y)] = Tile(room_piece=(Element.FLOOR, Direction.NONE))
    return tiles


class Room(BaseModel):
    """A representation of a room.

    Parameters
    ----------
    tiles
        The room tiles as a mapping from coordinates to Tile objects.
    """

    tiles: Dict[Tuple[int, int], Tile] = Field(default_factory=_create_empty_room)

    # Override BaseModel.__init__(), to convert any string keys in 'tiles'
    # to tuples. This is needed to deserialize a JSON room.
    def __init__(self, **kwargs):
        if "tiles" in kwargs:
            new_tiles = {}
            for key, value in kwargs["tiles"].items():
                if isinstance(key, str):
                    new_key = tuple(
                        [int(coord) for coord in key.strip("()").split(",")]
                    )
                    new_tiles[new_key] = value
                else:
                    new_tiles[key] = value
            kwargs["tiles"] = new_tiles
        super().__init__(**kwargs)

    # Override BaseModel.dict(), to convert the keys in 'tiles' to strings.
    # This is needed to serialize it as JSON.
    def dict(self, **kwargs):
        as_dict = super().dict(**kwargs)
        new_tiles = {}
        for key, value in as_dict["tiles"].items():
            new_tiles[str(key)] = value
        as_dict["tiles"] = new_tiles
        return as_dict

    def place_element(self, element, direction, position, end_position=None):
        """Place an element, like in the editor.

        No effort is made to mimic the behavior of the editor in terms of
        whether an element can be placed. If an element already exists in
        the same layer, it will be overwritten.

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
        elif element in FLOOR_CONTROLS:
            layer = "floor_control"
        elif element in CHECKPOINTS:
            layer = "checkpoints"
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
                tile = copy.deepcopy(self.tiles[(x, y)])
                setattr(tile, layer, (element, direction))
                self.tiles[(x, y)] = tile

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
            pos for pos, tile in self.tiles.items() if element in tile.get_elements()
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

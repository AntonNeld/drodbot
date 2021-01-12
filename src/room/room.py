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
                # Cannot place things on same layer as something else, unless either is
                # a floor.
                if (
                    getattr(tile, layer)[0] not in [Element.FLOOR, Element.NOTHING]
                ) and element != Element.FLOOR:
                    continue
                non_beethro_monsters = [
                    e for e in MONSTERS if e not in [Element.BEETHRO]
                ]
                conflicts_with_monsters = [Element.WALL, Element.ORB]
                if (
                    set(tile.get_elements()) & set(conflicts_with_monsters)
                    and element in non_beethro_monsters
                ):
                    continue
                if (
                    set(tile.get_elements()) & set(non_beethro_monsters)
                    and element in conflicts_with_monsters
                ):
                    continue
                # TODO: Implement more conditions where elements block each other
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

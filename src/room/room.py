import copy
from pydantic import BaseModel, Field
from typing import Dict, Tuple

from common import ROOM_WIDTH_IN_TILES, ROOM_HEIGHT_IN_TILES, Action
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
from util import direction_after


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

    def do_actions(self, actions):
        """Do multiple actions, and return a copy of the room after the actions.

        Parameters
        ----------
        actions
            The actions to perform.

        Returns
        -------
        A copy of the room after having performed the actions.
        """
        room = self.copy(deep=True)
        for action in actions:
            room._do_action_in_place(action)
        return room

    def do_action(self, action, in_place=False):
        """Do an action, and return a copy of the room after the action.

        The room after will match the result of performing an
        action in the actual game.

        Parameters
        ----------
        action
            The action to perform.
        in_place
            Whether to modify the room in place. The room will still be
            returned. Use this if you will not use the old room and performance
            is critical.

        Returns
        -------
        A copy of the room after having performed the action. If `in_place`
        is True, return the same room instance.
        """
        if in_place:
            room = self
        else:
            room = self.copy(deep=True)
        room._do_action_in_place(action)
        return room

    def _do_action_in_place(self, action):
        # TODO: This should use DRODLib from the DROD source instead of
        # reimplementing everything.
        x, y = self.find_player()
        direction = self.tiles[(x, y)].monster[1]
        pos_after = (x, y)
        if action == Action.N:
            pos_after = (x, y - 1)
        elif action == Action.NE:
            pos_after = (x + 1, y - 1)
        elif action == Action.E:
            pos_after = (x + 1, y)
        elif action == Action.SE:
            pos_after = (x + 1, y + 1)
        elif action == Action.S:
            pos_after = (x, y + 1)
        elif action == Action.SW:
            pos_after = (x - 1, y + 1)
        elif action == Action.W:
            pos_after = (x - 1, y)
        elif action == Action.NW:
            pos_after = (x - 1, y - 1)
        elif action in [Action.CW, Action.CCW]:
            direction = direction_after([action], direction)
        if self.tiles[pos_after].is_passable():
            self.tiles[(x, y)].monster = (Element.NOTHING, Direction.NONE)
            self.tiles[pos_after].monster = (Element.BEETHRO, direction)

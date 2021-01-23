from pydantic import BaseModel
from typing import Dict, Tuple

from common import Action
from .element import ElementType, Beethro, element_from_apparent
from .tile import Tile
from util import direction_after, position_in_direction


class Room(BaseModel):
    """A representation of a room.

    Parameters
    ----------
    tiles
        The room tiles as a mapping from coordinates to Tile objects.
    """

    tiles: Dict[Tuple[int, int], Tile]

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
            pos
            for pos, tile in self.tiles.items()
            if element in tile.get_element_types()
        ]

    def find_player(self):
        """Find the coordinates of the player.

        Returns
        -------
        The coordinates of the player, as an (x, y) tuple.
        """
        beethros = self.find_coordinates(ElementType.BEETHRO)
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
        position = self.find_player()
        direction = self.tiles[position].monster.direction
        pos_after = position
        if action in [Action.CW, Action.CCW]:
            direction = direction_after([action], direction)
        else:
            pos_after = position_in_direction(position, action)
        if self.tiles[pos_after].is_passable():
            self.tiles[position].monster = None
            self.tiles[pos_after].monster = Beethro(direction=direction)

    @staticmethod
    def from_apparent_tiles(apparent_tiles):
        """Create a room from apparent tiles.

        Not all information will be present in the beginning, only
        what can be seen from a screenshot.

        Parameters
        ----------
        apparent_tiles
            A dict mapping coordinates to ApparentTile instances.

        Returns
        -------
        A new room.
        """
        return Room(
            tiles={
                key: Tile(
                    room_piece=element_from_apparent(*tile.room_piece),
                    floor_control=element_from_apparent(*tile.floor_control),
                    checkpoint=element_from_apparent(*tile.checkpoint),
                    item=element_from_apparent(*tile.item),
                    monster=element_from_apparent(*tile.monster),
                )
                for key, tile in apparent_tiles.items()
            }
        )

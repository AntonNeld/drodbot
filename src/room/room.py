from pydantic import BaseModel
from typing import Dict, Tuple

from common import Action, ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from .element import (
    ElementType,
    OrbEffectType,
    UndirectionalElement,
    Beethro,
    element_from_apparent,
    element_to_apparent,
)
from .tile import Tile
from .apparent_tile import ApparentTile
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

    def do_actions(self, actions, in_place=False):
        """Do multiple actions, and return a copy of the room after the actions.

        Parameters
        ----------
        actions
            The actions to perform.
        in_place
            Whether to modify the room in place. The room will still be
            returned. Use this if you will not use the old room and performance
            is critical.

        Returns
        -------
        A copy of the room after having performed the actions.
        """
        if in_place:
            room = self
        else:
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
        sword_position = position_in_direction(pos_after, direction)
        if (
            sword_position[0] >= 0
            and sword_position[0] < ROOM_WIDTH_IN_TILES
            and sword_position[1] >= 0
            and sword_position[1] < ROOM_HEIGHT_IN_TILES
        ):
            under_sword = self.tiles[sword_position]
            if (
                under_sword.item is not None
                and under_sword.item.element_type == ElementType.ORB
            ):
                for effect, pos in under_sword.item.effects:
                    if self.tiles[pos].room_piece is None:
                        raise RuntimeError(
                            f"Orb at {sword_position} tried to {effect} element "
                            f"at {pos}, but nothing is there"
                        )
                    if self.tiles[pos].room_piece.element_type not in [
                        ElementType.YELLOW_DOOR,
                        ElementType.YELLOW_DOOR_OPEN,
                    ]:
                        raise RuntimeError(
                            f"Orb at {sword_position} tried to {effect} element "
                            f"at {pos}, but it is a "
                            f"{self.tiles[pos].room_piece.element_type}"
                        )
                    if effect == OrbEffectType.OPEN:
                        self.tiles[pos].room_piece = UndirectionalElement(
                            element_type=ElementType.YELLOW_DOOR_OPEN
                        )
                    elif effect == OrbEffectType.CLOSE:
                        self.tiles[pos].room_piece = UndirectionalElement(
                            element_type=ElementType.YELLOW_DOOR
                        )
                    # Toggle
                    elif (
                        self.tiles[pos].room_piece.element_type
                        == ElementType.YELLOW_DOOR
                    ):
                        self.tiles[pos].room_piece = UndirectionalElement(
                            element_type=ElementType.YELLOW_DOOR_OPEN
                        )
                    else:
                        self.tiles[pos].room_piece = UndirectionalElement(
                            element_type=ElementType.YELLOW_DOOR
                        )

    def to_apparent_tiles(self):
        """Create apparent tiles from a room.

        Returns
        -------
        A dict mapping coordinates to ApparentTile instances.
        """
        return {
            key: ApparentTile(
                room_piece=element_to_apparent(tile.room_piece),
                floor_control=element_to_apparent(tile.floor_control),
                checkpoint=element_to_apparent(tile.checkpoint),
                item=element_to_apparent(tile.item),
                monster=element_to_apparent(tile.monster),
            )
            for key, tile in self.tiles.items()
        }

    @staticmethod
    def from_apparent_tiles(apparent_tiles, orb_effects=None):
        """Create a room from apparent tiles.

        Not all information will be present in the beginning, only
        what can be seen without making any moves.

        Parameters
        ----------
        apparent_tiles
            A dict mapping coordinates to ApparentTile instances.
        orb_effects
            An optional dict mapping coordinates to (orb_effect, (x, y)),
            that gives the effects of orbs in the room.

        Returns
        -------
        A new room.
        """
        room = Room(
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
        if orb_effects is not None:
            for position, effects in orb_effects.items():
                room.tiles[position].item.effects = effects
        return room

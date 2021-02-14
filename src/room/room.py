from pydantic import BaseModel, Field
from typing import List

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
from room_simulator import simulate_action


class Room(BaseModel):
    """A representation of a room.

    Parameters
    ----------
    tiles
        The room tiles as a list of lists containing Tile objects.
    """

    tiles: List[List[Tile]] = Field(
        default_factory=lambda: [
            [
                Tile(room_piece=UndirectionalElement(element_type=ElementType.FLOOR))
                for y in range(ROOM_HEIGHT_IN_TILES)
            ]
            for x in range(ROOM_WIDTH_IN_TILES)
        ]
    )

    def tile_at(self, position):
        """Return the tile at the given position.

        Parameters
        ----------
        position
            A tuple (x, y).

        Returns
        -------
        The tile at that position.
        """
        x, y = position
        return self.tiles[x][y]

    def find_coordinates(self, element):
        """Find the coordinates of all elements of a type.

        Parameters
        ----------
        element
            The element type to find the coordinates of.

        Returns
        -------
        The coordinates of all elements of that type, as a list of (x, y) tuples.
        """
        return [
            (x, y)
            for x, columns in enumerate(self.tiles)
            for y, tile in enumerate(columns)
            if element in tile.get_element_types()
        ]

    def find_player(self):
        """Find the coordinates of the player.

        Returns
        -------
        A tuple ((x, y), direction).
        """
        beethros = self.find_coordinates(ElementType.BEETHRO)
        if len(beethros) < 1:
            raise RuntimeError("Cannot find Beethro")
        if len(beethros) > 1:
            raise RuntimeError(f"Too many Beethros: {beethros}")
        position = beethros[0]
        direction = self.tile_at(position).monster.direction
        return position, direction

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
        # Do nothing with the result for now
        simulate_action(0, action.value)

        position, direction = self.find_player()
        pos_after = position
        if action in [Action.CW, Action.CCW]:
            direction = direction_after([action], direction)
        else:
            pos_after = position_in_direction(position, action)
        if self.tile_at(pos_after).is_passable():
            self.tile_at(position).monster = None
            self.tile_at(pos_after).monster = Beethro(direction=direction)
        sword_position = position_in_direction(pos_after, direction)
        if (
            sword_position[0] >= 0
            and sword_position[0] < ROOM_WIDTH_IN_TILES
            and sword_position[1] >= 0
            and sword_position[1] < ROOM_HEIGHT_IN_TILES
        ):
            under_sword = self.tile_at(sword_position)
            if (
                under_sword.item is not None
                and under_sword.item.element_type == ElementType.ORB
            ):
                for effect, pos in under_sword.item.effects:
                    if self.tile_at(pos).room_piece is None:
                        raise RuntimeError(
                            f"Orb at {sword_position} tried to {effect} element "
                            f"at {pos}, but nothing is there"
                        )
                    if self.tile_at(pos).room_piece.element_type not in [
                        ElementType.YELLOW_DOOR,
                        ElementType.YELLOW_DOOR_OPEN,
                    ]:
                        raise RuntimeError(
                            f"Orb at {sword_position} tried to {effect} element "
                            f"at {pos}, but it is a "
                            f"{self.tile_at(pos).room_piece.element_type}"
                        )
                    if effect == OrbEffectType.OPEN:
                        self.tile_at(pos).room_piece = UndirectionalElement(
                            element_type=ElementType.YELLOW_DOOR_OPEN
                        )
                    elif effect == OrbEffectType.CLOSE:
                        self.tile_at(pos).room_piece = UndirectionalElement(
                            element_type=ElementType.YELLOW_DOOR
                        )
                    # Toggle
                    elif (
                        self.tile_at(pos).room_piece.element_type
                        == ElementType.YELLOW_DOOR
                    ):
                        self.tile_at(pos).room_piece = UndirectionalElement(
                            element_type=ElementType.YELLOW_DOOR_OPEN
                        )
                    else:
                        self.tile_at(pos).room_piece = UndirectionalElement(
                            element_type=ElementType.YELLOW_DOOR
                        )

    def to_apparent_tiles(self):
        """Create apparent tiles from a room.

        Returns
        -------
        A dict mapping coordinates to ApparentTile instances.
        """
        return {
            (x, y): ApparentTile(
                room_piece=element_to_apparent(tile.room_piece),
                floor_control=element_to_apparent(tile.floor_control),
                checkpoint=element_to_apparent(tile.checkpoint),
                item=element_to_apparent(tile.item),
                monster=element_to_apparent(tile.monster),
            )
            for x, columns in enumerate(self.tiles)
            for y, tile in enumerate(columns)
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
        room = Room()
        for (x, y), tile in apparent_tiles.items():
            room.tiles[x][y] = Tile(
                room_piece=element_from_apparent(*tile.room_piece),
                floor_control=element_from_apparent(*tile.floor_control),
                checkpoint=element_from_apparent(*tile.checkpoint),
                item=element_from_apparent(*tile.item),
                monster=element_from_apparent(*tile.monster),
            )

        if orb_effects is not None:
            for position, effects in orb_effects.items():
                room.tile_at(position).item.effects = effects
        return room

from pydantic import BaseModel, Field, validator
from typing import List

from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from room_simulator import ElementType, Element, Tile
from .apparent_tile import ApparentTile, element_from_apparent, element_to_apparent
from .dict_conversion import tile_to_dict, tile_from_dict
import room_simulator


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
                Tile(room_piece=Element(element_type=ElementType.FLOOR))
                for y in range(ROOM_HEIGHT_IN_TILES)
            ]
            for x in range(ROOM_WIDTH_IN_TILES)
        ]
    )

    class Config:
        json_encoders = {Tile: tile_to_dict}
        arbitrary_types_allowed = True

    @validator("tiles", pre=True)
    def parse_tiles(cls, v):
        return [
            [
                (tile if isinstance(tile, Tile) else tile_from_dict(tile))
                for tile in column
            ]
            for column in v
        ]

    def copy(self, deep=False):
        """Copy the room.

        Override this with a stupid replacement, since we can't pickle types from
        C++. Since this is temporary, there is no sense making the types pickleable.

        Parameters
        ----------
        deep
            Set to true for deep copy.

        Returns
        -------
        A copy of the room.
        """
        if not deep:
            return super().copy()
        return Room.parse_raw(self.json())

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

    def _get_element_types(self, x, y):
        """Get the types of all elements in a tile.

        ElementType.NOTHING is not included.

        Returns
        -------
        A list of all element types in the tile.
        """
        return [
            e.element_type
            for e in [
                self.tile_at((x, y)).room_piece,
                self.tile_at((x, y)).floor_control,
                self.tile_at((x, y)).checkpoint,
                self.tile_at((x, y)).item,
                self.tile_at((x, y)).monster,
            ]
            if e.element_type != ElementType.NOTHING
        ]

    def is_passable(self, x, y):
        """Check whether a tile is passable.

        It currently does not take into account force arrows, or
        whether doors can be opened.

        Returns
        -------
        Whether the tile is passable or not.
        """
        return (
            not set(
                [
                    ElementType.WALL,
                    ElementType.MASTER_WALL,
                    ElementType.OBSTACLE,
                    ElementType.YELLOW_DOOR,
                    ElementType.BLUE_DOOR,
                    ElementType.GREEN_DOOR,
                    ElementType.ORB,
                    ElementType.PIT,
                ]
            )
            & set(self._get_element_types(x, y))
        )

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
            if element in self._get_element_types(x, y)
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
        room_after = room_simulator.simulate_action(self._to_simulator_room(), action)
        self._set_from_simulator_room(room_after)

    def _to_simulator_room(self):
        simulator_room = []
        for column in self.tiles:
            simulator_column = []
            for tile in column:
                simulator_tile = room_simulator.Tile()
                simulator_tile.room_piece = tile.room_piece
                simulator_tile.floor_control = tile.floor_control
                simulator_tile.checkpoint = tile.checkpoint
                simulator_tile.item = tile.item
                simulator_tile.monster = tile.monster
                simulator_column.append(simulator_tile)
            simulator_room.append(simulator_column)

        return simulator_room

    def _set_from_simulator_room(self, simulator_room):
        tiles = []
        for x, simulator_column in enumerate(simulator_room):
            column = []
            for y, simulator_tile in enumerate(simulator_column):
                room_piece = simulator_tile.room_piece
                floor_control = simulator_tile.floor_control
                checkpoint = simulator_tile.checkpoint
                item = simulator_tile.item
                monster = simulator_tile.monster
                column.append(
                    Tile(
                        room_piece=room_piece,
                        floor_control=floor_control,
                        checkpoint=checkpoint,
                        item=item,
                        monster=monster,
                    )
                )
            tiles.append(column)
        self.tiles = tiles

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
                room.tile_at(position).item.orb_effects = effects
        return room

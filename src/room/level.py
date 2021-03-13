from itertools import groupby
from typing import Dict, Tuple

from pydantic import BaseModel, validator

from .room import Room
from .dict_conversion import room_from_dict
from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from room_simulator import Action


class Level(BaseModel):
    """A representation of a level.

    Parameters
    ----------
    rooms
        The rooms, indexed by coordinates. The coordinates do not
        necessarily correspond to the in-game coordinates.
    """

    rooms: Dict[Tuple[int, int], Room] = {}

    class Config:
        arbitrary_types_allowed = True

    @validator("rooms", pre=True)
    def parse_rooms(cls, v):
        return {
            key: v[key] if isinstance(v[key], Room) else room_from_dict(v[key])
            for key in v
        }

    # Override BaseModel.__init__(), to convert any string keys in 'rooms'
    # to tuples. This is needed to deserialize a JSON level.
    def __init__(self, **kwargs):
        if "rooms" in kwargs:
            new_rooms = {}
            for key, value in kwargs["rooms"].items():
                if isinstance(key, str):
                    new_key = tuple(
                        [int(coord) for coord in key.strip("()").split(",")]
                    )
                    new_rooms[new_key] = value
                else:
                    new_rooms[key] = value
            kwargs["rooms"] = new_rooms
        super().__init__(**kwargs)

    # Override BaseModel.dict(), to convert the keys in 'rooms' to strings.
    # This is needed to serialize it as JSON.
    def dict(self, **kwargs):
        as_dict = super().dict(**kwargs)
        new_rooms = {}
        for key, value in as_dict["rooms"].items():
            new_rooms[str(key)] = value
        as_dict["rooms"] = new_rooms
        return as_dict

    def find_element(self, element):
        """Find instances of an element in the level.

        Parameters
        ----------
        element
            The element to find.

        Returns
        -------
        A list of tuples ((room_x, room_y), (tile_x, tile_y)).
        """
        return_coordinates = []
        for room_position, room in self.rooms.items():
            return_coordinates.extend(
                [
                    (room_position, tile_position)
                    for tile_position in room.find_coordinates(element)
                ]
            )
        return return_coordinates

    def find_uncrossed_edges(self):
        """Find edges to unexplored rooms.

        Returns
        -------
        A list of tuples ((room_x, room_y), (tile_x, tile_y)).
        """
        uncrossed_edge_tiles = []
        for room_pos, room in self.rooms.items():
            room_x, room_y = room_pos
            if (room_x, room_y - 1) not in self.rooms:
                uncrossed_edge_tiles.extend(
                    [
                        (room_pos, (x, 0))
                        for x in range(ROOM_WIDTH_IN_TILES)
                        if room.is_passable(x, 0)
                    ]
                )
            if (room_x + 1, room_y) not in self.rooms:
                uncrossed_edge_tiles.extend(
                    [
                        (room_pos, (ROOM_WIDTH_IN_TILES - 1, y))
                        for y in range(ROOM_HEIGHT_IN_TILES)
                        if room.is_passable(ROOM_WIDTH_IN_TILES - 1, y)
                    ]
                )
            if (room_x, room_y + 1) not in self.rooms:
                uncrossed_edge_tiles.extend(
                    [
                        (room_pos, (x, ROOM_HEIGHT_IN_TILES - 1))
                        for x in range(ROOM_WIDTH_IN_TILES)
                        if room.is_passable(x, ROOM_HEIGHT_IN_TILES - 1)
                    ]
                )
            if (room_x - 1, room_y) not in self.rooms:
                uncrossed_edge_tiles.extend(
                    [
                        (room_pos, (0, y))
                        for y in range(ROOM_HEIGHT_IN_TILES)
                        if room.is_passable(0, y)
                    ]
                )
        return uncrossed_edge_tiles

    def get_room_exits(self, room_position):
        """Get all valid exits from a room.

        If the room on the other side is not known, it is not a valid exit.
        If an entrance/exit is wider than one tile, only return one tile from it.

        Parameters
        ----------
        room_position
            The room to exit.

        Returns
        -------
        A list of tuples:
            (tile_position_from, movement_action, (room_position_to, tile_position_to))
        """
        room_x, room_y = room_position
        exits = []
        for (
            target_room,
            movement_action,
            edge_length,
            x_current_room,
            y_current_room,
            x_next_room,
            y_next_room,
        ) in [
            # North edge
            (
                (room_x, room_y - 1),
                Action.N,
                ROOM_WIDTH_IN_TILES,
                None,
                0,
                None,
                ROOM_HEIGHT_IN_TILES - 1,
            ),
            # East edge
            (
                (room_x + 1, room_y),
                Action.E,
                ROOM_HEIGHT_IN_TILES,
                ROOM_WIDTH_IN_TILES - 1,
                None,
                0,
                None,
            ),
            # South edge
            (
                (room_x, room_y + 1),
                Action.S,
                ROOM_WIDTH_IN_TILES,
                None,
                ROOM_HEIGHT_IN_TILES - 1,
                None,
                0,
            ),
            # West edge
            (
                (room_x - 1, room_y),
                Action.W,
                ROOM_HEIGHT_IN_TILES,
                0,
                None,
                ROOM_WIDTH_IN_TILES - 1,
                None,
            ),
        ]:
            if target_room in self.rooms:
                free_coords = [
                    n
                    for n in range(edge_length)
                    if self.rooms[room_position].is_passable(
                        n if x_current_room is None else x_current_room,
                        n if y_current_room is None else y_current_room,
                    )
                    and self.rooms[target_room].is_passable(
                        n if x_next_room is None else x_next_room,
                        n if y_next_room is None else y_next_room,
                    )
                ]
                # Find continuous regions
                groups = groupby(enumerate(free_coords), lambda x: x[0] - x[1])
                for _, group in groups:
                    group_as_list = list(group)
                    middle_coord = group_as_list[len(group_as_list) // 2][1]
                    exits.append(
                        (
                            (
                                middle_coord
                                if x_current_room is None
                                else x_current_room,
                                middle_coord
                                if y_current_room is None
                                else y_current_room,
                            ),
                            movement_action,
                            (
                                target_room,
                                (
                                    middle_coord
                                    if x_next_room is None
                                    else x_next_room,
                                    middle_coord
                                    if y_next_room is None
                                    else y_next_room,
                                ),
                            ),
                        )
                    )
        return exits

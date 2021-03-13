from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from room_simulator import ElementType, Element, Tile
import room_simulator


class Room:
    """A representation of a room.

    Parameters
    ----------
    tiles
        The room tiles as a list of lists containing Tile objects. Defaults to
        an empty room with normal floor.
    _simulator_room
        A simulator room with the actual data. Only to be used in copy().

    """

    def __init__(self, tiles=None, _simulator_room=None):
        if _simulator_room is not None:
            self._room = _simulator_room
        elif tiles is not None:
            self._room = room_simulator.Room(tiles=tiles)
        else:
            self._room = room_simulator.Room(
                tiles=[
                    [
                        Tile(room_piece=Element(element_type=ElementType.FLOOR))
                        for y in range(ROOM_HEIGHT_IN_TILES)
                    ]
                    for x in range(ROOM_WIDTH_IN_TILES)
                ]
            )

    def copy(self):
        """Copy the room.

        Returns
        -------
        A copy of the room.
        """
        return Room(_simulator_room=self._room.copy())

    def get_tile(self, position):
        """Return the tile at the given position.

        Parameters
        ----------
        position
            A tuple (x, y).

        Returns
        -------
        The tile at that position.
        """
        return self._room.get_tile(position)

    def set_tile(self, position, tile):
        """Set the tile at the given position.

        Parameters
        ----------
        position
            A tuple (x, y).
        tile
            The tile to set.
        """
        self._room.set_tile(position, tile)

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
                self.get_tile((x, y)).room_piece,
                self.get_tile((x, y)).floor_control,
                self.get_tile((x, y)).checkpoint,
                self.get_tile((x, y)).item,
                self.get_tile((x, y)).monster,
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
            for x in range(ROOM_WIDTH_IN_TILES)
            for y in range(ROOM_HEIGHT_IN_TILES)
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
        direction = self.get_tile(position).monster.direction
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
            room = self.copy()
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
            room = self.copy()
        room._do_action_in_place(action)
        return room

    def _do_action_in_place(self, action):
        self._room = room_simulator.simulate_action(self._room, action)

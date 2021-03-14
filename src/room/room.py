import room_simulator


class Room:
    """A representation of a room.

    Parameters
    ----------
    tiles
        The room tiles as a list of lists containing Tile objects. Either this
        or _simulator_room must be set.
    _simulator_room
        A simulator room with the actual data. Only to be used internally.

    """

    def __init__(self, tiles=None, _simulator_room=None):
        if _simulator_room is not None:
            self._room = _simulator_room
        elif tiles is not None:
            self._room = room_simulator.Room(tiles=tiles)
        else:
            raise RuntimeError("Either tiles or _simulator_room must be set")

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

    def is_passable(self, x, y):
        """Check whether a tile is passable.

        It currently does not take into account force arrows, or
        whether doors can be opened.

        Parameters
        ----------
        x
            The x coordinate.
        y
            The y coordinate.

        Returns
        -------
        Whether the tile is passable or not.
        """
        return self._room.is_passable(x, y)

    def find_coordinates(self, element_type):
        """Find the coordinates of all elements of a type.

        Parameters
        ----------
        element_type
            The element type to find the coordinates of.

        Returns
        -------
        The coordinates of all elements of that type, as a list of (x, y) tuples.
        """
        return self._room.find_coordinates(element_type)

    def find_player(self):
        """Find the coordinates of the player.

        Returns
        -------
        A tuple ((x, y), direction).
        """
        return self._room.find_player()

    def do_action(self, action):
        """Do an action, and return a copy of the room after the action.

        The room after will match the result of performing an
        action in the actual game.

        Parameters
        ----------
        action
            The action to perform.

        Returns
        -------
        A copy of the room after having performed the action. If `in_place`
        is True, return the same room instance.
        """
        return Room(_simulator_room=room_simulator.simulate_action(self._room, action))

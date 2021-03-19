from .room_conversion import room_from_apparent_tiles


class RoomInterpreter:
    """This is used to keep track of the possible contents of a room.

    Parameters
    ----------
    classifier
        A tile classifier.
    """

    def __init__(self, classifier, play_interface):
        self._classifier = classifier
        self._interface = play_interface

    async def get_initial_room(self, return_debug_images=False):
        """Get an initial guess of a room by taking a screenshot.

        Parameters
        ----------
        return_debug_images
            If True, return an additional list of tuples (name, debug_image).

        Returns
        -------
        room
            A room.
        debug_images
            Only returned if `return_debug_images` is True. A list of (name, image).
        """
        if return_debug_images:
            tile_contents, orb_effects, debug_images = await self._interface.get_view(
                return_debug_images=True
            )
        else:
            tile_contents, orb_effects = await self._interface.get_view()
        room = room_from_apparent_tiles(tile_contents, orb_effects)

        if return_debug_images:
            return room, debug_images
        return room

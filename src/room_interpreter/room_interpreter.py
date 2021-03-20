import numpy
from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES, TILE_SIZE

from room_simulator import ElementType
from .room_conversion import room_from_apparent_tiles, element_to_apparent
from tile_classifier import ApparentTile
from util import extract_tiles


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
            room_image, minimap, debug_images = await self._interface.get_room_image(
                return_debug_images=True
            )
        else:
            room_image, minimap = await self._interface.get_room_image()

        tiles, minimap_colors = extract_tiles(room_image, minimap)

        tile_contents = self._classifier.classify_tiles(tiles, minimap_colors)

        orb_positions = [
            pos
            for pos, tile in tile_contents.items()
            if tile.item[0] == ElementType.ORB
        ]
        # A position we can click to get rid of the displayed orb effects
        # TODO: Handle the case when there is no such position
        free_position = next(
            pos
            for pos, tile in tile_contents.items()
            if tile.item[0] != ElementType.ORB
            and tile.room_piece[0]
            not in [ElementType.YELLOW_DOOR, ElementType.YELLOW_DOOR_OPEN]
        )
        if return_debug_images:
            orb_effects, effects_debug_images = await self._interface.get_orb_effects(
                orb_positions, room_image, free_position, return_debug_images=True
            )
            debug_images.extend(effects_debug_images)
        else:
            orb_effects = await self._interface.get_orb_effects(
                orb_positions, room_image, free_position
            )

        room = room_from_apparent_tiles(tile_contents, orb_effects)

        if return_debug_images:
            return room, debug_images
        return room

    def reconstruct_room_image(self, room):
        """Get a reconstructed image of a room.

        Parameters
        ----------
        room
            The room.

        Returns
        -------
        An image of the room.
        """

        room_image = numpy.zeros(
            (TILE_SIZE * ROOM_HEIGHT_IN_TILES, TILE_SIZE * ROOM_WIDTH_IN_TILES, 3),
            dtype=numpy.uint8,
        )
        for x in range(ROOM_WIDTH_IN_TILES):
            for y in range(ROOM_HEIGHT_IN_TILES):
                tile = room.get_tile((x, y))
                tile_image = self._classifier.get_tile_image(
                    ApparentTile(
                        room_piece=element_to_apparent(tile.room_piece),
                        floor_control=element_to_apparent(tile.floor_control),
                        checkpoint=element_to_apparent(tile.checkpoint),
                        item=element_to_apparent(tile.item),
                        monster=element_to_apparent(tile.monster),
                    )
                )
                room_image[
                    y * TILE_SIZE : (y + 1) * TILE_SIZE,
                    x * TILE_SIZE : (x + 1) * TILE_SIZE,
                    :,
                ] = tile_image
        return room_image

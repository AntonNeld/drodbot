from enum import Enum
import numpy
from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES, TILE_SIZE

from room_simulator import ElementType, Direction
from .room_conversion import room_from_apparent_tiles, element_to_apparent
from tile_classifier import ApparentTile
from util import extract_tiles


class RoomText(str, Enum):
    """The text that pops up when entering a room."""

    NOTHING = ""
    EXIT_LEVEL = "Exit level"
    SECRET_ROOM = "Secret room"


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
        room_text
            The room text that pops up on room entry.
        debug_images
            Only returned if `return_debug_images` is True. A list of (name, image).
        """
        if return_debug_images:
            room_image, minimap, debug_images = await self._interface.get_room_image(
                return_debug_images=True
            )
        else:
            room_image, minimap = await self._interface.get_room_image()

        if return_debug_images:
            room_text, room_text_debug_images = get_room_text(
                room_image, return_debug_images=True
            )
            debug_images.extend(room_text_debug_images)
        else:
            room_text = get_room_text(room_image)

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

        monster_positions = [
            pos
            for pos, tile in tile_contents.items()
            if tile.monster[0] not in [ElementType.NOTHING, ElementType.BEETHRO]
        ]

        if return_debug_images:
            (
                movement_orders,
                layer_counts,
                order_debug_images,
            ) = await self._interface.get_right_click_info(
                monster_positions,
                return_debug_images=True,
            )
            debug_images.extend(order_debug_images)
        else:
            movement_orders, layer_counts = await self._interface.get_right_click_info(
                monster_positions
            )

        adjusted_tile_contents = _adjust_tile_contents(tile_contents, layer_counts)

        room = room_from_apparent_tiles(
            adjusted_tile_contents, orb_effects, movement_orders
        )

        if return_debug_images:
            return room, room_text, debug_images
        return room, room_text

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


def _adjust_tile_contents(tile_contents, layer_counts):
    adjusted_tile_contents = {key: value for (key, value) in tile_contents.items()}
    for position, layer_count in layer_counts.items():
        tile = tile_contents[position]
        layer_contents = [
            tile.monster,
            tile.item,
            tile.checkpoint,
            tile.floor_control,
            tile.room_piece,
        ]
        apparent_layer_count = 5 - [t[0] for t in layer_contents].count(
            ElementType.NOTHING
        )
        if apparent_layer_count != layer_count:
            print(
                f"{apparent_layer_count} non-empty layers detected at {position}, "
                f"but right-click says {layer_count}"
            )
            if apparent_layer_count < layer_count:
                print(f"Apparent layers are fewer at {position}, nothing to do")
            else:
                claimed_layers = 1  # The room piece is always there
                for i in range(len(layer_contents) - 1):  # Skip the room_piece
                    if layer_contents[i][0] != ElementType.NOTHING:
                        if claimed_layers == layer_count:
                            print(f"Removing {layer_contents[i][0].name} at {position}")
                            layer_contents[i] = (ElementType.NOTHING, Direction.NONE)
                        else:
                            claimed_layers += 1
                adjusted_tile_contents[position] = ApparentTile(
                    monster=layer_contents[0],
                    item=layer_contents[1],
                    checkpoint=layer_contents[2],
                    floor_control=layer_contents[3],
                    room_piece=layer_contents[4],
                )

    return adjusted_tile_contents


def get_room_text(room_image, return_debug_images=False):
    """Get the text that sometimes pops up when entering a room.

    Parameters
    ----------
    room_image
        The room extracted from a screenshot.
    return_debug_images
        Whether to return debug images.

    Returns
    -------
    room_text
        A RoomText instance.
    debug_images
        Debug images, only returned if return_debug_images is True.
    """
    if return_debug_images:
        debug_images = []
    room_text = RoomText.NOTHING
    if return_debug_images:
        return room_text, debug_images
    return room_text

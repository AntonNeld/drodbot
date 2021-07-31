import re
import asyncio
from enum import Enum
import numpy
import scipy.ndimage

from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES, TILE_SIZE
from room_simulator import ElementType, Direction
from .room_conversion import room_from_apparent_tiles, element_to_apparent
from tile_classifier import ApparentTile
from util import element_layer, extract_tiles, find_color

_TEXT_TO_ELEMENT = {
    "Wall": ElementType.WALL,
    "Pit": ElementType.PIT,
    "Masterwall": ElementType.MASTER_WALL,
    "Yellowdoor": ElementType.YELLOW_DOOR,
    "Roomcleargate": ElementType.GREEN_DOOR,
    "Levelcleargate": ElementType.BLUE_DOOR,
    "Trapdoorgate": ElementType.RED_DOOR,
    "Trapdoor": ElementType.TRAPDOOR,
    "Stairs": ElementType.STAIRS,
    "Stairsup": ElementType.STAIRS,
    "Forcearrow": ElementType.FORCE_ARROW,
    "Checkpoint": ElementType.CHECKPOINT,
    "Orb": ElementType.ORB,
    "Mimicpotion": ElementType.MIMIC_POTION,
    "Invisibilitypotion": ElementType.INVISIBILITY_POTION,
    "Scroll": ElementType.SCROLL,
    "Obstacle": ElementType.OBSTACLE,
    "Player": ElementType.BEETHRO,
    "Roach": ElementType.ROACH,
    "Roachqueen": ElementType.ROACH_QUEEN,
    "Roachegg": ElementType.ROACH_EGG,
    "Evileye": ElementType.EVIL_EYE,
    "Wraithwing": ElementType.WRAITHWING,
    "Spider": ElementType.SPIDER,
    "Goblin": ElementType.GOBLIN,
    "Brain": ElementType.BRAIN,
    "Tarbaby": ElementType.TAR_BABY,
    "Mimic": ElementType.MIMIC,
    "Token": ElementType.CONQUER_TOKEN,
    "Floor": ElementType.FLOOR,
    "Alternatefloor": ElementType.FLOOR,
    "Floormosaic": ElementType.FLOOR,
    "Road": ElementType.FLOOR,
    "Grass": ElementType.FLOOR,
    "Dirtfloor": ElementType.FLOOR,
}
_TEXT_TO_DIRECTION = {
    "South": Direction.S,
    "North": Direction.N,
    "West": Direction.W,
    "East": Direction.E,
    "northwest": Direction.NW,
    "northeast": Direction.NE,
    "southwest": Direction.SW,
    "southeast": Direction.SE,
}


class RoomText(str, Enum):
    """The text that pops up when entering a room."""

    NOTHING = ""
    EXIT_LEVEL = "Exit level"
    SECRET_ROOM = "Secret room"
    EXIT_LEVEL_AND_SECRET_ROOM = "Exit level & Secret room"


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

        if room_text != RoomText.NOTHING:
            # Wait until the text is gone and try again
            await asyncio.sleep(3)
            if return_debug_images:
                (
                    room_image,
                    minimap,
                    after_text_debug_images,
                ) = await self._interface.get_room_image(return_debug_images=True)
                debug_images.extend(
                    [
                        (f"{name}, second try", image)
                        for (name, image) in after_text_debug_images
                    ]
                )
            else:
                room_image, minimap = await self._interface.get_room_image()

        if return_debug_images:
            (
                tile_contents,
                detected_style,
                easy_tiles_debug_images,
            ) = self._classifier.get_easy_tiles(room_image, return_debug_images=True)
            debug_images.extend(easy_tiles_debug_images)
        else:
            tile_contents, detected_style = self._classifier.get_easy_tiles(room_image)

        tiles, minimap_colors = extract_tiles(
            room_image, minimap, skip_coords=tile_contents.keys()
        )

        classified_tiles, difficult_positions = self._classifier.classify_tiles(
            tiles, minimap_colors, room_style=detected_style
        )
        tile_contents.update(classified_tiles)

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
        to_right_click = sorted(
            list(set(monster_positions + difficult_positions)),
            key=lambda p: p[0] * 100 + p[1],
        )

        if return_debug_images:
            (texts, order_debug_images,) = await self._interface.get_right_click_text(
                to_right_click,
                return_debug_images=True,
            )
            debug_images.extend(order_debug_images)
        else:
            texts = await self._interface.get_right_click_text(to_right_click)
        movement_orders = {}
        for pos, text in texts.items():
            order = _get_movement_order(text)
            if order is not None:
                movement_orders[pos] = order

        adjusted_tile_contents = _adjust_tile_contents(tile_contents, texts)

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


def _adjust_tile_contents(tile_contents, texts):
    """Adjust the tile content based on the right-click text.

    Parameters
    ----------
    tile_contents
        Map of position to ApparentTile.
    texts
        Map of position to right-click text.

    Returns
    -------
    Adjusted tile contents.
    """
    adjusted_tile_contents = {key: value for (key, value) in tile_contents.items()}
    for position, text in texts.items():
        tile = tile_contents[position]
        lines = text.split("\n")
        for line in lines[1:]:  # First line is position
            parts = line.split("(")
            element_text = parts[0]
            element = _TEXT_TO_ELEMENT[element_text]
            layer = element_layer(element)
            parenthesis_text = parts[1].replace(")", "") if len(parts) > 1 else ""
            if parenthesis_text in _TEXT_TO_DIRECTION:
                direction = _TEXT_TO_DIRECTION[parenthesis_text]
            else:
                # This probably works, since the only directional elements where
                # it's not included in the text are monsters. Hopefully we've
                # detected those properly since they are on top.
                # (The exception is roach eggs, where NONE is correct)
                direction = Direction.NONE
            if parenthesis_text == "open":
                open_doors = {
                    ElementType.YELLOW_DOOR: ElementType.YELLOW_DOOR_OPEN,
                    ElementType.BLUE_DOOR: ElementType.BLUE_DOOR_OPEN,
                    ElementType.GREEN_DOOR: ElementType.GREEN_DOOR_OPEN,
                    ElementType.RED_DOOR: ElementType.RED_DOOR_OPEN,
                }
                element = open_doors[element]
            if element != getattr(tile, layer)[0]:
                # Awake and sleeping evil eyes have the same text
                if not (
                    element == ElementType.EVIL_EYE
                    and getattr(tile, layer)[0] == ElementType.EVIL_EYE_AWAKE
                ):
                    setattr(tile, layer, (element, direction))

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
    yellow_pixels = find_color(room_image, (254, 254, 0))
    if return_debug_images:
        debug_images.append(("Yellow pixels", yellow_pixels))
    dilated = scipy.ndimage.binary_dilation(
        yellow_pixels, structure=numpy.ones((1, 20))
    )
    if return_debug_images:
        debug_images.append(("Binary dilated", dilated))
    labels, num_labels = scipy.ndimage.label(dilated)
    if return_debug_images:
        debug_images.append(("Text regions", labels * 255 // max(num_labels, 1)))
    if num_labels == 0:
        room_text = RoomText.NOTHING
    elif num_labels == 4:
        room_text = RoomText.EXIT_LEVEL_AND_SECRET_ROOM
    elif num_labels == 2:
        # We're assuming here that the leftmost label is 1. This seems to hold.
        size_ratio = numpy.sum(labels == 1) / numpy.sum(labels == 2)
        if size_ratio > 1:
            room_text = RoomText.SECRET_ROOM
        else:
            room_text = RoomText.EXIT_LEVEL
    else:
        print("Saw an unexpected number of yellow regions, investigate manually!")
        room_text = RoomText.NOTHING

    if room_text != RoomText.NOTHING:
        print(f"Detected room text: {room_text.value}")

    if return_debug_images:
        return room_text, debug_images
    return room_text


def _get_movement_order(text):
    match = re.search(r"\(#.*\)", text)
    if match is None:
        return None
    # We use zero-indexing, but displayed movement order starts at 1
    return int(match.group()[2:-1]) - 1

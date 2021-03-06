import numpy
import pyautogui

from common import (
    UserError,
    ROOM_HEIGHT_IN_TILES,
    ROOM_WIDTH_IN_TILES,
    TILE_SIZE,
)
from .consts import ROOM_ORIGIN_X, ROOM_ORIGIN_Y
from util import find_color

_ROOM_UPPER_EDGE_COLOR = (32, 60, 74)
_ROOM_UPPER_EDGE_LENGTH = 838
_ROOM_UPPER_EDGE_START_X = 162
_ROOM_UPPER_EDGE_START_Y = 39
_DROD_WINDOW_WIDTH = 1024
_DROD_WINDOW_HEIGHT = 768

_OVERLAY_COLOR = (0, 255, 0)
_OVERLAY_WIDTH = 5

_MINIMAP_ROOM_ORIGIN_X = 61
_MINIMAP_ROOM_ORIGIN_Y = 631


async def get_drod_window(return_debug_images=False):
    """Take a screenshot and find the DROD window.

    Only the inside of the window is included, not the window
    bar which is OS-dependent.

    Parameters
    ----------
    return_debug_images
        If this is True, return an additional list of (name, debug_image).

    Returns
    -------
    origin_x : int
        The X coordinate of upper left corner of the window.
    origin_y : int
        The Y coordinate of upper left corner of the window.
    image : numpy.ndarray
        The DROD window.
    debug_images
        Debug images. Only returned if `return_debug_images` is True.
    """
    if return_debug_images:
        debug_images = []
    raw_image = numpy.array(pyautogui.screenshot())
    if return_debug_images:
        debug_images.append(("Screenshot", raw_image))

    # Try finding the upper edge of the room, which is a long line of constant color
    correct_color = find_color(raw_image, _ROOM_UPPER_EDGE_COLOR)
    if return_debug_images:
        debug_images.append(("Find upper edge color", correct_color))

    lines = _find_horizontal_lines(correct_color, _ROOM_UPPER_EDGE_LENGTH)
    if return_debug_images:
        # We can't show the line coordinates directly, so we'll overlay the line on
        # the screenshot
        with_line = raw_image.copy()
        for (start_x, start_y, end_x, _) in lines:
            # Since we're only dealing with horizontal lines, we can do the overlay
            # by indexing the array directly
            with_line[
                start_y : start_y + _OVERLAY_WIDTH, start_x:end_x, :
            ] = _OVERLAY_COLOR
        debug_images.append(("Find upper edge line", with_line))

    if len(lines) > 1:
        raise UserError("Cannot identify DROD window, too many candidate lines")
    elif len(lines) == 0:
        raise UserError("Cannot identify DROD window, is it open and unblocked?")

    # Extract the window
    line_start_x = lines[0][0]
    line_start_y = lines[0][1]
    window_start_x = line_start_x - _ROOM_UPPER_EDGE_START_X
    window_start_y = line_start_y - _ROOM_UPPER_EDGE_START_Y
    window_end_x = window_start_x + _DROD_WINDOW_WIDTH
    window_end_y = window_start_y + _DROD_WINDOW_HEIGHT
    drod_window = raw_image[
        window_start_y:window_end_y,
        window_start_x:window_end_x,
        :,
    ]
    if return_debug_images:
        return window_start_x, window_start_y, drod_window, debug_images
    return window_start_x, window_start_y, drod_window


def extract_room(window_image):
    """Extract the room from a window image.

    Parameters
    ----------
    window_image
        The window to extract the room from.

    Returns
    -------
    An image of the room.
    """
    room_end_x = ROOM_ORIGIN_X + ROOM_WIDTH_IN_TILES * TILE_SIZE
    room_end_y = ROOM_ORIGIN_Y + ROOM_HEIGHT_IN_TILES * TILE_SIZE
    room_image = window_image[ROOM_ORIGIN_Y:room_end_y, ROOM_ORIGIN_X:room_end_x, :]
    return room_image


def extract_minimap(window_image):
    """Extract the room minimap from a window image.

    Parameters
    ----------
    window_image
        The window to extract the room minimap from.

    Returns
    -------
    An image of the room minimap.
    """
    room_end_x = _MINIMAP_ROOM_ORIGIN_X + ROOM_WIDTH_IN_TILES
    room_end_y = _MINIMAP_ROOM_ORIGIN_Y + ROOM_HEIGHT_IN_TILES
    minimap_room_image = window_image[
        _MINIMAP_ROOM_ORIGIN_Y:room_end_y, _MINIMAP_ROOM_ORIGIN_X:room_end_x, :
    ]
    return minimap_room_image


def reconstruct_from_tiles(tiles):
    """Reconstruct a room image given the tiles.

    Parameters
    ----------
    tiles
        A dict mapping (x, y) coordinates to tile images. The images
        can be in color or grayscale.

    Returns
    -------
    A room image.
    """
    tile = list(tiles.values())[0]
    if len(tile.shape) == 3:
        room_image = numpy.zeros(
            (
                ROOM_HEIGHT_IN_TILES * TILE_SIZE,
                ROOM_WIDTH_IN_TILES * TILE_SIZE,
                tile.shape[2],
            ),
            dtype=numpy.uint8,
        )
    else:
        room_image = numpy.zeros(
            (ROOM_HEIGHT_IN_TILES * TILE_SIZE, ROOM_WIDTH_IN_TILES * TILE_SIZE),
            dtype=numpy.uint8,
        )
    for x in range(ROOM_WIDTH_IN_TILES):
        for y in range(ROOM_HEIGHT_IN_TILES):
            start_x = x * TILE_SIZE
            end_x = (x + 1) * TILE_SIZE
            start_y = y * TILE_SIZE
            end_y = (y + 1) * TILE_SIZE
            room_image[start_y:end_y, start_x:end_x] = tiles[(x, y)]
    return room_image


def _find_horizontal_lines(boolean_array, length):
    # Pad, to find lines that start or end at the edges
    int_array = numpy.pad(boolean_array.astype(int), (0, 1))
    # Coords of the first pixel in each line
    starts = numpy.argwhere(numpy.diff(int_array) == 1) + (0, 1)
    # Coords of the pixel after the last in each line
    ends = numpy.argwhere(numpy.diff(int_array) == -1) + (0, 1)
    lines = []
    for coords in starts:
        start_x = coords[1]
        start_y = coords[0]
        end_x = [e[1] for e in ends if e[0] == start_y]
        if start_x + length in end_x and not any(
            [x > start_x and x < start_x + length for x in end_x]
        ):
            # We have an uninterrupted line of the specified length
            lines.append((start_x, start_y, start_x + length, start_y))
    return lines

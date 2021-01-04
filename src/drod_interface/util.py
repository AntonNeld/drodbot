import numpy
import pyautogui

from common import (
    ImageProcessingStep,
    UserError,
    ROOM_HEIGHT_IN_TILES,
    ROOM_WIDTH_IN_TILES,
    TILE_SIZE,
)
from .consts import ROOM_ORIGIN_X, ROOM_ORIGIN_Y

ROOM_UPPER_EDGE_COLOR = (32, 60, 74)  # Also known as #203c4a
ROOM_UPPER_EDGE_LENGTH = 838
ROOM_UPPER_EDGE_START_X = 162
ROOM_UPPER_EDGE_START_Y = 39
DROD_WINDOW_WIDTH = 1024
DROD_WINDOW_HEIGHT = 768

OVERLAY_COLOR = (0, 255, 0)
OVERLAY_WIDTH = 5

MINIMAP_ROOM_ORIGIN_X = 61
MINIMAP_ROOM_ORIGIN_Y = 631


async def get_drod_window(stop_after=None):
    """Take a screenshot and find the DROD window.

    Only the inside of the window is included, not the window
    bar which is OS-dependent.

    Parameters
    ----------
    stop_after
        If this is not None, stop after the given step and
        return the current state of the image. If the origin
        coordinates have not been determined, they will be (0, 0).

    Returns
    -------
    origin_x : int
        The X coordinate of upper left corner of the window.
    origin_y : int
        The Y coordinate of upper left corner of the window.
    image : numpy.ndarray
        The DROD window, or an earlier image depending on `stop_after`.
    """
    raw_image = numpy.array(pyautogui.screenshot())
    if stop_after == ImageProcessingStep.SCREENSHOT:
        return 0, 0, raw_image

    # Try finding the upper edge of the room, which is a long line of constant color
    correct_color = _find_color(raw_image, ROOM_UPPER_EDGE_COLOR)
    if stop_after == ImageProcessingStep.FIND_UPPER_EDGE_COLOR:
        return 0, 0, correct_color

    lines = _find_horizontal_lines(correct_color, ROOM_UPPER_EDGE_LENGTH)
    if stop_after == ImageProcessingStep.FIND_UPPER_EDGE_LINE:
        # We can't show the line coordinates directly, so we'll overlay the line on
        # the screenshot
        with_line = raw_image.copy()
        for (start_x, start_y, end_x, _) in lines:
            # Since we're only dealing with horizontal lines, we can do the overlay
            # by indexing the array directly
            with_line[
                start_y : start_y + OVERLAY_WIDTH, start_x:end_x, :
            ] = OVERLAY_COLOR
        return 0, 0, with_line

    if len(lines) > 1:
        raise UserError("Cannot identify DROD window, too many candidate lines")
    elif len(lines) == 0:
        raise UserError("Cannot identify DROD window, is it open and unblocked?")

    # Extract the window
    line_start_x = lines[0][0]
    line_start_y = lines[0][1]
    window_start_x = line_start_x - ROOM_UPPER_EDGE_START_X
    window_start_y = line_start_y - ROOM_UPPER_EDGE_START_Y
    window_end_x = window_start_x + DROD_WINDOW_WIDTH
    window_end_y = window_start_y + DROD_WINDOW_HEIGHT
    drod_window = raw_image[
        window_start_y:window_end_y,
        window_start_x:window_end_x,
        :,
    ]
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
    room_end_x = MINIMAP_ROOM_ORIGIN_X + ROOM_WIDTH_IN_TILES
    room_end_y = MINIMAP_ROOM_ORIGIN_Y + ROOM_HEIGHT_IN_TILES
    minimap_room_image = window_image[
        MINIMAP_ROOM_ORIGIN_Y:room_end_y, MINIMAP_ROOM_ORIGIN_X:room_end_x, :
    ]
    return minimap_room_image


def extract_tiles(room_image, minimap_image):
    """Extract tiles from a room image.

    Parameters
    ----------
    room_image
        The room to extract tiles from.
    minimap_image
        The minimap to extract minimap colors from.

    Returns
    -------
    tiles
        A dict with coordinates as keys and tile images as values.
    colors
        A dict with coordinates as keys and (r, g, b) tuples as values.
    """
    tiles = {}
    colors = {}
    for x in range(ROOM_WIDTH_IN_TILES):
        for y in range(ROOM_HEIGHT_IN_TILES):
            start_x = x * TILE_SIZE
            end_x = (x + 1) * TILE_SIZE
            start_y = y * TILE_SIZE
            end_y = (y + 1) * TILE_SIZE
            tiles[(x, y)] = room_image[start_y:end_y, start_x:end_x, :]
            color = minimap_image[y, x, :]
            colors[(x, y)] = (int(color[0]), int(color[1]), int(color[2]))
    return tiles, colors


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


def _find_color(image, color):
    r = image[:, :, 0]
    g = image[:, :, 1]
    b = image[:, :, 2]
    return numpy.logical_and.reduce(
        [
            r == color[0],
            g == color[1],
            b == color[2],
        ]
    )


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

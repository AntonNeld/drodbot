import tkinter
from tkinter import ttk

import cv2
import numpy

from common import (
    ROOM_HEIGHT_IN_TILES,
    ROOM_WIDTH_IN_TILES,
    TILE_SIZE,
)
from room_simulator import ElementType, Direction

# These are overlaid over the room to show tile classifications
ELEMENT_CHARACTERS = {
    ElementType.UNKNOWN: "?",
    ElementType.WALL: "#",
    ElementType.PIT: ",",
    ElementType.MASTER_WALL: "M",
    ElementType.YELLOW_DOOR: "Y",
    ElementType.YELLOW_DOOR_OPEN: "y",
    ElementType.GREEN_DOOR: "G",
    ElementType.GREEN_DOOR_OPEN: "g",
    ElementType.BLUE_DOOR: "B",
    ElementType.BLUE_DOOR_OPEN: "b",
    ElementType.STAIRS: ">",
    ElementType.FORCE_ARROW: "^",
    ElementType.CHECKPOINT: "x",
    ElementType.ORB: "O",
    ElementType.SCROLL: "s",
    ElementType.OBSTACLE: "+",
    ElementType.BEETHRO: "B",
    ElementType.ROACH: "R",
    ElementType.CONQUER_TOKEN: "C",
    ElementType.FLOOR: ".",
    ElementType.NOTHING: " ",
}


def apparent_tile_to_text(tile):
    """Describe an apparent tile in a human-friendly format.

    Parameters
    ----------
    tile
        The apparent tile representation.

    Returns
    -------
    Human-readable text describing the tile contents.
    """
    lines = [
        f"Room piece: {_format_apparent_element(tile.room_piece)}",
        f"Floor control: {_format_apparent_element(tile.floor_control)}",
        f"Checkpoint: {_format_apparent_element(tile.checkpoint)}",
        f"Item: {_format_apparent_element(tile.item)}",
        f"Monster: {_format_apparent_element(tile.monster)}",
    ]
    return "\n".join(lines)


def _format_apparent_element(pair):
    element, direction = pair
    if direction == Direction.NONE:
        return element.name
    else:
        return f"{element.name} {direction.name}"


def tile_to_text(tile):
    """Describe the tile in a human-friendly format.

    Parameters
    ----------
    tile
        The tile.

    Returns
    -------
    A string describing the tile.
    """
    lines = [
        f"Room piece: {_format_element(tile.room_piece)}",
        f"Floor control: {_format_element(tile.floor_control)}",
        f"Checkpoint: {_format_element(tile.checkpoint)}",
        f"Item: {_format_element(tile.item)}",
        f"Monster: {_format_element(tile.monster)}",
    ]
    return "\n".join(lines)


def _format_element(element):
    element_type = element.element_type
    direction = element.direction
    if direction == Direction.NONE:
        return element_type.name
    else:
        return f"{element_type.name} {direction.name}"


def annotate_room_image_with_tile_contents(image, room):
    """Get an image of a room, annotated with tile contents.

    Parameters
    ----------
    image
        The original room image.
    room
        A Room instance.

    Returns
    -------
    A grayscale image of the room, with the elements in each tile
    overlaid as characters. The character that corresponds to each
    element is defined in ELEMENT_CHARACTERS.
    """
    annotated_image = numpy.zeros(image.shape, dtype=numpy.uint8)
    for x in range(ROOM_WIDTH_IN_TILES):
        for y in range(ROOM_HEIGHT_IN_TILES):
            tile_image = image[
                y * TILE_SIZE : (y + 1) * TILE_SIZE, x * TILE_SIZE : (x + 1) * TILE_SIZE
            ]
            tile = room.get_tile((x, y))
            # Convert the tile to grayscale to make the text stand out.
            # We're converting it back to RGB so we can add the text, but
            # the tile will still look grayscale since we lose color information.
            modified_tile = cv2.cvtColor(
                cv2.cvtColor(tile_image, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB
            )
            for element in [
                tile.room_piece,
                tile.floor_control,
                tile.checkpoint,
                tile.item,
                tile.monster,
            ]:
                cv2.putText(
                    modified_tile,
                    ELEMENT_CHARACTERS[element.element_type],
                    (0, tile_image.shape[0]),
                    cv2.FONT_HERSHEY_PLAIN,
                    2,
                    (255, 50, 0),
                )
            annotated_image[
                y * TILE_SIZE : (y + 1) * TILE_SIZE, x * TILE_SIZE : (x + 1) * TILE_SIZE
            ] = modified_tile
    return annotated_image


class ScrollableFrame(ttk.Frame):
    """A frame with a scrollbar.

    Taken from https://blog.tecladocode.com/tkinter-scrollable-frames/.
    This should not itself be set as the parent for widgets. Instead the
    attribute `scrollable_frame` should be used.

    Parameters
    ----------
    root
        The parent of the frame.

    Attributes
    ----------
    scrollable_frame
        The internal frame. Set this as the parent for anything inside
        this frame.
    """

    def __init__(self, root):
        super().__init__(root)
        canvas = tkinter.Canvas(self)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

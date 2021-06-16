import tkinter
from tkinter import ttk

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
    return_str = element_type.name
    if direction != Direction.NONE:
        return_str = f"{return_str} {direction.name}"
    if element.monster_id is not None:
        return_str = f"{return_str} ({element.monster_id})"
    return return_str


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

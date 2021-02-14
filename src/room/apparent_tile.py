from pydantic import BaseModel
from typing import Tuple

from .element import ElementType, Direction


class ApparentTile(BaseModel):
    """A representation of a tile, as interpreted from a screenshot.

    This contains information about what element is visible in each layer,
    as a tuple of (ElementType, Direction).

    Parameters
    ----------
    room_piece
        The element in the "room pieces" layer.
    floor_control
        The element in the "floor controls" layer (excluding checkpoints and lighting).
    checkpoint
        The element in the checkpoints layer.
    item
        The element in the "items" layer.
    monster
        The element in the "monsters" layer.
    """

    room_piece: Tuple[ElementType, Direction]
    floor_control: Tuple[ElementType, Direction] = (
        ElementType.NOTHING,
        Direction.NONE,
    )
    checkpoint: Tuple[ElementType, Direction] = (
        ElementType.NOTHING,
        Direction.NONE,
    )
    item: Tuple[ElementType, Direction] = (
        ElementType.NOTHING,
        Direction.NONE,
    )
    monster: Tuple[ElementType, Direction] = (
        ElementType.NOTHING,
        Direction.NONE,
    )

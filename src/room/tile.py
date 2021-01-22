from pydantic import BaseModel
from typing import Tuple

from .element import ElementType, Direction


class Tile(BaseModel):
    """A representation of a tile.

    This contains information about what element is in each layer, as a tuple of
    (ElementType, Direction).

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

    def get_elements(self):
        """Get all elements in the tile.

        ElementType.NOTHING is skipped.

        Returns
        -------
        A list of all elements (without directions) in the tile.
        """
        return [
            e[0]
            for e in [
                self.room_piece,
                self.floor_control,
                self.checkpoint,
                self.item,
                self.monster,
            ]
            if e[0] != ElementType.NOTHING
        ]

    def is_passable(self):
        """Check whether the tile is passable.

        It currently does not take into account force arrows, or
        whether doors can be opened.

        Returns
        -------
        Whether the tile is passable or not.
        """
        return (
            not set(
                [
                    ElementType.WALL,
                    ElementType.MASTER_WALL,
                    ElementType.OBSTACLE,
                    ElementType.YELLOW_DOOR,
                    ElementType.BLUE_DOOR,
                    ElementType.GREEN_DOOR,
                    ElementType.ORB,
                    ElementType.PIT,
                ]
            )
            & set(self.get_elements())
        )

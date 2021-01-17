from pydantic import BaseModel
from typing import Tuple

from .element import Element, Direction


class Tile(BaseModel):
    """A representation of a tile.

    This contains information about what element is in each layer, as a tuple of
    (Element, Direction).

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

    room_piece: Tuple[Element, Direction]
    floor_control: Tuple[Element, Direction] = (Element.NOTHING, Direction.NONE)
    checkpoint: Tuple[Element, Direction] = (Element.NOTHING, Direction.NONE)
    item: Tuple[Element, Direction] = (Element.NOTHING, Direction.NONE)
    monster: Tuple[Element, Direction] = (Element.NOTHING, Direction.NONE)

    def get_elements(self):
        """Get all elements in the tile.

        Element.NOTHING is skipped.

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
            if e[0] != Element.NOTHING
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
                    Element.WALL,
                    Element.MASTER_WALL,
                    Element.OBSTACLE,
                    Element.YELLOW_DOOR,
                    Element.BLUE_DOOR,
                    Element.GREEN_DOOR,
                    Element.ORB,
                    Element.PIT,
                ]
            )
            & set(self.get_elements())
        )

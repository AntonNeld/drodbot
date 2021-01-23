from pydantic import BaseModel
from typing import Optional

from .element import ElementType, Element


class Tile(BaseModel):
    """A representation of a tile.

    This contains information about what element is in each layer.
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

    room_piece: Element
    floor_control: Optional[Element]
    checkpoint: Optional[Element]
    item: Optional[Element]
    monster: Optional[Element]

    def get_element_types(self):
        """Get the types of all elements in the tile.

        ElementType.NOTHING is not included.

        Returns
        -------
        A list of all element types in the tile.
        """
        return [
            e.element_type
            for e in [
                self.room_piece,
                self.floor_control,
                self.checkpoint,
                self.item,
                self.monster,
            ]
            if e is not None
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
            & set(self.get_element_types())
        )

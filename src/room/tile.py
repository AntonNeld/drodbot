from dataclasses import dataclass
import json
from typing import Tuple

from .element import Element, Direction


@dataclass
class Tile:
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

    def to_json(self):
        """Encodes the tile as JSON.

        Returns
        -------
        The JSON-encoded tile.
        """

        return json.dumps(
            {
                "room_piece": [e.value for e in self.room_piece],
                "floor_control": [e.value for e in self.floor_control],
                "checkpoint": [e.value for e in self.checkpoint],
                "item": [e.value for e in self.item],
                "monster": [e.value for e in self.monster],
            }
        )

    @staticmethod
    def from_json(json_string):
        """Creates a Tile object from a JSON representation.

        Parameters
        ----------
        json_string
            A JSON-encoded Tile object.

        Returns
        -------
        A Tile object.
        """
        json_dict = json.loads(json_string)
        constructor_args = {
            key: _element_tuple_from_json(value) for key, value in json_dict.items()
        }
        return Tile(**constructor_args)


def _element_tuple_from_json(pair):
    element = next(e for e in Element if e.value == pair[0])
    direction = next(d for d in Direction if d.value == pair[1])
    return (element, direction)

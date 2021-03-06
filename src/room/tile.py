from pydantic import BaseModel, Field, validator

from .dict_conversion import element_from_dict
from room_simulator import ElementType, Element


def _parse_element(element):
    if isinstance(element, Element):
        return element
    return element_from_dict(element)


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

    room_piece: Element = Field(default_factory=lambda: Element())
    floor_control: Element = Field(default_factory=lambda: Element())
    checkpoint: Element = Field(default_factory=lambda: Element())
    item: Element = Field(default_factory=lambda: Element())
    monster: Element = Field(default_factory=lambda: Element())

    _parse_room_piece = validator("room_piece", allow_reuse=True, pre=True)(
        _parse_element
    )
    _parse_floor_control = validator("floor_control", allow_reuse=True, pre=True)(
        _parse_element
    )
    _parse_checkpoint = validator("checkpoint", allow_reuse=True, pre=True)(
        _parse_element
    )
    _parse_item = validator("item", allow_reuse=True, pre=True)(_parse_element)
    _parse_monster = validator("monster", allow_reuse=True, pre=True)(_parse_element)

    class Config:
        arbitrary_types_allowed = True


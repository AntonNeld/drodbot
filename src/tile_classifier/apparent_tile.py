from typing import Tuple

from pydantic import BaseModel, validator

from room_simulator import ElementType, Direction


def _parse_pair(v):
    element_type = v[0] if isinstance(v[0], ElementType) else getattr(ElementType, v[0])
    direction = v[1] if isinstance(v[1], Direction) else getattr(Direction, v[1])
    return (element_type, direction)


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

    _parse_room_piece = validator("room_piece", allow_reuse=True, pre=True)(_parse_pair)
    _parse_floor_control = validator("floor_control", allow_reuse=True, pre=True)(
        _parse_pair
    )
    _parse_checkpoint = validator("checkpoint", allow_reuse=True, pre=True)(_parse_pair)
    _parse_item = validator("item", allow_reuse=True, pre=True)(_parse_pair)
    _parse_monster = validator("monster", allow_reuse=True, pre=True)(_parse_pair)

    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ElementType: lambda e: e.name, Direction: lambda d: d.name}

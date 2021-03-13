from pydantic import BaseModel, validator
from typing import Tuple

from common import ROOM_WIDTH_IN_TILES, ROOM_HEIGHT_IN_TILES
from room import Room
from room_simulator import ElementType, Direction, Element, Tile


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


def element_from_apparent(element_type, direction, orb_effects=None):
    """Create an element from an element type and a direction.

    Some information may be missing initially.

    Parameters
    ----------
    element_type
        The element type.
    direction
        The direction.

    Returns
    -------
    An element or None.
    """
    if orb_effects is not None:
        return Element(
            element_type=element_type, direction=direction, orb_effects=orb_effects
        )
    return Element(element_type=element_type, direction=direction)


def element_to_apparent(element):
    """Create an apparent element from an element.

    Parameters
    ----------
    element
        The element.

    Returns
    -------
    A tuple (ElementType, Direction).
    """
    return (element.element_type, element.direction)


def room_from_apparent_tiles(apparent_tiles, orb_effects=None):
    """Create a room from apparent tiles.

    Not all information will be present in the beginning, only
    what can be seen without making any moves.

    Parameters
    ----------
    apparent_tiles
        A dict mapping coordinates to ApparentTile instances.
    orb_effects
        An optional dict mapping coordinates to (orb_effect, (x, y)),
        that gives the effects of orbs in the room.

    Returns
    -------
    A new room.
    """
    tiles = []
    for x in range(ROOM_WIDTH_IN_TILES):
        column = []
        for y in range(ROOM_HEIGHT_IN_TILES):
            tile = apparent_tiles[(x, y)]
            column.append(
                Tile(
                    room_piece=element_from_apparent(*tile.room_piece),
                    floor_control=element_from_apparent(*tile.floor_control),
                    checkpoint=element_from_apparent(*tile.checkpoint),
                    item=element_from_apparent(*tile.item),
                    monster=element_from_apparent(*tile.monster),
                )
            )
        tiles.append(column)

    if orb_effects is not None:
        for (x, y), effects in orb_effects.items():
            tiles[x][y].item.orb_effects = effects

    return Room(tiles=tiles)

from common import ROOM_WIDTH_IN_TILES, ROOM_HEIGHT_IN_TILES
from room_simulator import Element, Tile, Room, ElementType


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
    monster_id = 0
    tiles = []
    for x in range(ROOM_WIDTH_IN_TILES):
        column = []
        for y in range(ROOM_HEIGHT_IN_TILES):
            tile = apparent_tiles[(x, y)]
            monster = element_from_apparent(*tile.monster)
            if monster.element_type not in [ElementType.NOTHING, ElementType.BEETHRO]:
                monster.monster_id = monster_id
                monster_id = monster_id + 1
            column.append(
                Tile(
                    room_piece=element_from_apparent(*tile.room_piece),
                    floor_control=element_from_apparent(*tile.floor_control),
                    checkpoint=element_from_apparent(*tile.checkpoint),
                    item=element_from_apparent(*tile.item),
                    monster=monster,
                )
            )
        tiles.append(column)

    if orb_effects is not None:
        for (x, y), effects in orb_effects.items():
            tiles[x][y].item.orb_effects = effects

    return Room(tiles=tiles)

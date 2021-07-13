from common import ROOM_WIDTH_IN_TILES, ROOM_HEIGHT_IN_TILES
from room_simulator import Element, Tile, Room, ElementType


def element_from_apparent(element_type, direction, orb_effects=None, turn_order=None):
    """Create an element from an element type and a direction.

    Some information may be missing initially.

    Parameters
    ----------
    element_type
        The element type.
    direction
        The direction.
    orb_effects
        Optional orb effects.
    turn_order
        Optional movement order

    Returns
    -------
    An element or None.
    """
    if orb_effects is not None:
        return Element(
            element_type=element_type, direction=direction, orb_effects=orb_effects
        )
    elif turn_order is not None:  # Orbs cannot move
        return Element(
            element_type=element_type, direction=direction, turn_order=turn_order
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


def room_from_apparent_tiles(apparent_tiles, orb_effects=None, movement_orders=None):
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
    movement_orders
        An optional dict mapping coordinates to ints, that gives
        the movement order of monsters in the room.

    Returns
    -------
    A new room.
    """
    monster_tiles = set()
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
            if tile.monster[0] not in (ElementType.NOTHING, ElementType.BEETHRO):
                monster_tiles.add((x, y))
        tiles.append(column)

    extra_orders = set(range(len(monster_tiles)))
    if movement_orders is not None:
        for (x, y), order in movement_orders.items():
            tiles[x][y].monster.turn_order = order
            extra_orders.remove(order)
            monster_tiles.remove((x, y))
    # Assign the leftover movement orders to the leftover monsters, if any
    for (x, y), order in zip(monster_tiles, extra_orders):
        tiles[x][y].monster.turn_order = order

    if orb_effects is not None:
        for (x, y), effects in orb_effects.items():
            tiles[x][y].item.orb_effects = effects

    return Room(tiles=tiles)

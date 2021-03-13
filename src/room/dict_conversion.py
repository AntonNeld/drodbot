from room_simulator import ElementType, Direction, OrbEffect, Element, Tile
from .room import Room


def element_to_dict(element):
    """Convert an element to a dict, for JSON serialization.

    Parameters
    ----------
    element
        The element.

    Returns
    -------
    A dict representation of the element.
    """
    return {
        "element_type": element.element_type.name,
        "direction": element.direction.name,
        "orb_effects": [(x, y, effect.name) for (x, y, effect) in element.orb_effects],
    }


def element_from_dict(element_dict):
    """Get an element from a dict representation, for JSON deserialization.

    Parameters
    ----------
    element_dict
        The dict representation of the element.

    Returns
    -------
    An element.
    """
    return Element(
        element_type=getattr(ElementType, element_dict["element_type"]),
        direction=getattr(Direction, element_dict["direction"]),
        orb_effects=[
            (x, y, getattr(OrbEffect, effect))
            for (x, y, effect) in element_dict["orb_effects"]
        ],
    )


def tile_to_dict(tile):
    """Convert a tile to a dict, for JSON serialization.

    Parameters
    ----------
    tile
        The tile.

    Returns
    -------
    A dict representation of the tile.
    """
    return {
        "room_piece": element_to_dict(tile.room_piece),
        "floor_control": element_to_dict(tile.floor_control),
        "checkpoint": element_to_dict(tile.checkpoint),
        "item": element_to_dict(tile.item),
        "monster": element_to_dict(tile.monster),
    }


def tile_from_dict(tile_dict):
    """Get a tile from a dict representation, for JSON deserialization.

    Parameters
    ----------
    tile_dict
        The dict representation of the tile.

    Returns
    -------
    A tile.
    """
    return Tile(
        room_piece=element_from_dict(tile_dict["room_piece"]),
        floor_control=element_from_dict(tile_dict["floor_control"]),
        checkpoint=element_from_dict(tile_dict["checkpoint"]),
        item=element_from_dict(tile_dict["item"]),
        monster=element_from_dict(tile_dict["monster"]),
    )


def room_to_dict(room):
    """Convert a room to a dict, for JSON serialization.

    Parameters
    ----------
    room
        The room.

    Returns
    -------
    A dict representation of the room.
    """
    return {"tiles": [[tile_to_dict(tile) for tile in column] for column in room.tiles]}


def room_from_dict(room_dict):
    """Get a room from a dict representation, for JSON deserialization.

    Parameters
    ----------
    room_dict
        The dict representation of the room.

    Returns
    -------
    A room.
    """
    return Room(
        tiles=[
            [tile_from_dict(tile_dict) for tile_dict in column]
            for column in room_dict["tiles"]
        ]
    )

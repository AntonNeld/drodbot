from room_simulator import ElementType, Direction, OrbEffect, Element, Tile


def element_to_dict(element):
    return {
        "element_type": element.element_type.name,
        "direction": element.direction.name,
        "orb_effects": [(x, y, effect.name) for (x, y, effect) in element.orb_effects],
    }


def element_from_dict(element_dict):
    return Element(
        element_type=getattr(ElementType, element_dict["element_type"]),
        direction=getattr(Direction, element_dict["direction"]),
        orb_effects=[
            (x, y, getattr(OrbEffect, effect))
            for (x, y, effect) in element_dict["orb_effects"]
        ],
    )


def tile_to_dict(tile):
    return {
        "room_piece": element_to_dict(tile.room_piece),
        "floor_control": element_to_dict(tile.floor_control),
        "checkpoint": element_to_dict(tile.checkpoint),
        "item": element_to_dict(tile.item),
        "monster": element_to_dict(tile.monster),
    }


def tile_from_dict(tile_dict):
    return Tile(
        room_piece=element_from_dict(tile_dict["room_piece"]),
        floor_control=element_from_dict(tile_dict["floor_control"]),
        checkpoint=element_from_dict(tile_dict["checkpoint"]),
        item=element_from_dict(tile_dict["item"]),
        monster=element_from_dict(tile_dict["monster"]),
    )

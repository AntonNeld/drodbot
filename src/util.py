from typing import Union

import numpy

from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES, TILE_SIZE
from room_simulator import (
    Direction,
    ElementType,
    Action,
    OrbEffect,
    Element,
    Tile,
    Room,
    OrObjective,
    ReachObjective,
    MonsterCountObjective,
    StabObjective,
)


def find_color(image, color):
    """Find all pixels with a specific color.

    Parameters
    ----------
    image
        The image to find the color in.
    color
        The color to find.

    Returns
    -------
    A boolean 2D numpy array, which is True where the image
    has the color and False elsewhere.
    """
    r = image[:, :, 0]
    g = image[:, :, 1]
    b = image[:, :, 2]
    return numpy.logical_and.reduce(
        [
            r == color[0],
            g == color[1],
            b == color[2],
        ]
    )


def extract_object(image, object_mask):
    """Crop an image to only contain an object.

    Parameters
    ----------
    image
        The image to extract the object from.
    object_mask
        True where the object is.

    Returns
    -------
    The cropped image.
    """
    rows = numpy.any(object_mask, axis=1)
    columns = numpy.any(object_mask, axis=0)
    ymin, ymax = numpy.where(rows)[0][[0, -1]]
    xmin, xmax = numpy.where(columns)[0][[0, -1]]
    return image[ymin : ymax + 1, xmin : xmax + 1]


def extract_tiles(room_image, minimap_image, skip_coords=None):
    """Extract tiles from a room image.

    Parameters
    ----------
    room_image
        The room to extract tiles from.
    minimap_image
        The minimap to extract minimap colors from.
    skip_coords
        If not None, skip these coordinates.

    Returns
    -------
    tiles
        A dict with coordinates as keys and tile images as values.
    colors
        A dict with coordinates as keys and (r, g, b) tuples as values.
    """
    tiles = {}
    colors = {}
    for x in range(ROOM_WIDTH_IN_TILES):
        for y in range(ROOM_HEIGHT_IN_TILES):
            if skip_coords is not None and (x, y) in skip_coords:
                continue
            start_x = x * TILE_SIZE
            end_x = (x + 1) * TILE_SIZE
            start_y = y * TILE_SIZE
            end_y = (y + 1) * TILE_SIZE
            tiles[(x, y)] = room_image[start_y:end_y, start_x:end_x, :]
            color = minimap_image[y, x, :]
            colors[(x, y)] = (int(color[0]), int(color[1]), int(color[2]))
    return tiles, colors


def direction_after(actions, direction):
    """Get the direction the player faces after the given actions.

    Parameters
    ----------
    actions
        The actions to take.
    direction
        The starting direction.

    Returns
    -------
    The resulting direction.
    """
    direction_to_number = {
        Direction.N: 0,
        Direction.NE: 1,
        Direction.E: 2,
        Direction.SE: 3,
        Direction.S: 4,
        Direction.SW: 5,
        Direction.W: 6,
        Direction.NW: 7,
    }
    number_to_direction = {
        0: Direction.N,
        1: Direction.NE,
        2: Direction.E,
        3: Direction.SE,
        4: Direction.S,
        5: Direction.SW,
        6: Direction.W,
        7: Direction.NW,
    }
    dir_number = direction_to_number[direction]
    for action in actions:
        if action == Action.CW:
            dir_number += 1
        elif action == Action.CCW:
            dir_number -= 1
    return number_to_direction[dir_number % 8]


def position_in_direction(original_position, direction):
    """Get the position in the given direction, relative to an original position.

    Parameters
    ----------
    original_position
        The original position as a tuple (x, y).
    direction
        The direction of the new position. Both Direcions
        and (movement) Actions are valid.

    Returns
    -------
    The new position as a tuple (x, y).
    """
    x, y = original_position
    if direction == Action.N or direction == Direction.N:
        return (x, y - 1)
    elif direction == Action.NE or direction == Direction.NE:
        return (x + 1, y - 1)
    elif direction == Action.E or direction == Direction.E:
        return (x + 1, y)
    elif direction == Action.SE or direction == Direction.SE:
        return (x + 1, y + 1)
    elif direction == Action.S or direction == Direction.S:
        return (x, y + 1)
    elif direction == Action.SW or direction == Direction.SW:
        return (x - 1, y + 1)
    elif direction == Action.W or direction == Direction.W:
        return (x - 1, y)
    elif direction == Action.NW or direction == Direction.NW:
        return (x - 1, y - 1)
    else:
        # Assume this is another action, which won't affect direction
        return (x, y)


def inside_room(position):
    """Check whether a position is inside the room.

    Parameters
    ----------
    position
        The (x, y) coordinates.

    Returns
    -------
    Whether the coordinates are inside the room.
    """
    x, y = position
    return x >= 0 and x < ROOM_WIDTH_IN_TILES and y >= 0 and y < ROOM_HEIGHT_IN_TILES


def element_layer(element_type):
    """Get the layer an element belongs to.

    Parameters
    ----------
    element_type
        The type of the element.

    Returns
    -------
    The layer as a string.
    """
    if element_type in [
        ElementType.WALL,
        ElementType.FLOOR,
        ElementType.PIT,
        ElementType.MASTER_WALL,
        ElementType.YELLOW_DOOR,
        ElementType.YELLOW_DOOR_OPEN,
        ElementType.GREEN_DOOR,
        ElementType.GREEN_DOOR_OPEN,
        ElementType.BLUE_DOOR,
        ElementType.BLUE_DOOR_OPEN,
        ElementType.RED_DOOR,
        ElementType.RED_DOOR_OPEN,
        ElementType.STAIRS,
        ElementType.TRAPDOOR,
    ]:
        return "room_piece"
    if element_type in [ElementType.FORCE_ARROW]:
        return "floor_control"
    if element_type in [ElementType.CHECKPOINT]:
        return "checkpoint"
    if element_type in [
        ElementType.CONQUER_TOKEN,
        ElementType.ORB,
        ElementType.SCROLL,
        ElementType.OBSTACLE,
        ElementType.MIMIC_POTION,
        ElementType.INVISIBILITY_POTION,
    ]:
        return "item"
    if element_type in [
        ElementType.BEETHRO,
        ElementType.ROACH,
        ElementType.ROACH_QUEEN,
        ElementType.ROACH_EGG,
        ElementType.EVIL_EYE,
        ElementType.EVIL_EYE_AWAKE,
        ElementType.SPIDER,
        ElementType.WRAITHWING,
        ElementType.GOBLIN,
        ElementType.TAR_BABY,
        ElementType.BRAIN,
        ElementType.MIMIC,
    ]:
        return "monster"
    if element_type in [ElementType.BEETHRO_SWORD, ElementType.MIMIC_SWORD]:
        return "swords"
    raise RuntimeError(f"{element_type} has no defined layer")


def expand_planning_solution(sub_objectives, objective_reacher):
    """Get a sequence of actions from a solution to a planning problem.

    Parameters
    ----------
    room
        The room.
    sub_objectives
        A list of objectives solving a planning problem.
    objective_reacher
        The objective reacher used when finding the solution,
        so we don't need to find the solutions to the sub-objectives
        again.

    Returns
    -------
    A list of actions reaching all sub-objectives in order.
    """
    actions = []
    objective_reacher.get_room_player().set_actions([])
    latest_room = objective_reacher.get_room_player().get_derived_room()
    for sub_objective in sub_objectives:
        sub_solution = objective_reacher.find_solution(latest_room, sub_objective)
        actions.extend(sub_solution.actions)
        latest_room = sub_solution.final_state
    return actions


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
        "turn_order": element.turn_order,
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
        turn_order=element_dict["turn_order"],
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
    return {
        "tiles": [
            [tile_to_dict(room.get_tile((x, y))) for y in range(ROOM_HEIGHT_IN_TILES)]
            for x in range(ROOM_WIDTH_IN_TILES)
        ]
    }


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


def objective_to_dict(
    objective: Union[OrObjective, ReachObjective, StabObjective, MonsterCountObjective]
):
    if isinstance(objective, OrObjective):
        return {
            "kind": "OrObjective",
            "objectives": [objective_to_dict(o) for o in objective.objectives],
        }
    if isinstance(objective, ReachObjective):
        return {"kind": "ReachObjective", "tiles": list(objective.tiles)}
    if isinstance(objective, StabObjective):
        return {"kind": "StabObjective", "tiles": list(objective.tiles)}
    if isinstance(objective, MonsterCountObjective):
        return {
            "kind": "MonsterCountObjective",
            "monsters": objective.monsters,
            "allow_less": objective.allow_less,
        }

import numpy

from common import ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES, TILE_SIZE
from room_simulator import Direction, ElementType, Action


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


def extract_tiles(room_image, minimap_image):
    """Extract tiles from a room image.

    Parameters
    ----------
    room_image
        The room to extract tiles from.
    minimap_image
        The minimap to extract minimap colors from.

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
        raise RuntimeError(f"Unknown direction {direction}")


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
        ElementType.STAIRS,
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
    ]:
        return "item"
    if element_type in [
        ElementType.BEETHRO,
        ElementType.ROACH,
    ]:
        return "monster"
    if element_type in [ElementType.BEETHRO_SWORD]:
        return "swords"
    raise RuntimeError(f"{element_type} has no defined layer")


def expand_planning_solution(room, sub_objectives, objective_reacher):
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
    latest_room = room
    for sub_objective in sub_objectives:
        sub_solution = objective_reacher.find_solution(latest_room, sub_objective)
        actions.extend(sub_solution.actions)
        latest_room = sub_solution.final_state
    return actions

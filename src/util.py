import numpy

from common import Action, ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from room import Direction


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

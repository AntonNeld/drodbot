import numpy

from common import Action
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

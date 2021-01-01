import cv2
import numpy

from common import Element, Direction, ImageProcessingStep, Tile

# We will have to revisit this logic to make sure we don't have false positives,
# but let's limit ourselves a few elements in the "Foundation" style for now:
# - Wall
# - Beethro (Let's guess that he's facing SE for now)
# - Conquer token
# - Floor
# This should be enough to solve mazes in that style


def classify_tile(tile_image, step=None):
    average_color = numpy.average(tile_image, (0, 1))
    if step == ImageProcessingStep.AVERAGE_TILE_COLOR:
        return None, numpy.ones(tile_image.shape) * average_color

    hsv_color = cv2.cvtColor(
        numpy.float32(numpy.ones((1, 1, 1)) * average_color), cv2.COLOR_RGB2HSV
    )
    hue = hsv_color[0, 0, 0]
    saturation = hsv_color[0, 0, 1]
    # If the saturation is low, it's probably empty floor
    if saturation < 0.1:
        tile = Tile(room_piece=(Element.FLOOR, Direction.NONE))
    # Else, if the hue is purplish, it's probably a wall
    elif hue > 275 and hue < 300:
        tile = Tile(room_piece=(Element.WALL, Direction.NONE))
    # Else, if the hue is yellowish, it's probably Beethro.
    elif hue > 33 and hue < 38:
        tile = Tile(
            room_piece=(Element.FLOOR, Direction.NONE),
            monster=(Element.BEETHRO, Direction.SE),
        )
    # If it's a little more green, it's probably Beethro standing on a conquer token
    elif hue > 38 and hue < 42:
        tile = Tile(
            room_piece=(Element.FLOOR, Direction.NONE),
            item=(Element.CONQUER_TOKEN, Direction.NONE),
            monster=(Element.BEETHRO, Direction.SE),
        )
    # Else, if the hue is greenish, it's probably a conquer token
    elif hue > 110 and hue < 120:
        tile = Tile(
            room_piece=(Element.FLOOR, Direction.NONE),
            item=(Element.CONQUER_TOKEN, Direction.NONE),
        )
    # If it's this other shade of green, it's probably a triggered conquer token
    elif hue > 95 and hue < 110:
        tile = Tile(
            room_piece=(Element.FLOOR, Direction.NONE),
            item=(Element.CONQUER_TOKEN, Direction.NONE),
        )
    else:
        print(f"Found unknown tile with hue {hue} and saturation {saturation}")
        tile = Tile(
            room_piece=(Element.UNKNOWN, Direction.UNKNOWN),
            floor_control=(Element.UNKNOWN, Direction.UNKNOWN),
            checkpoint=(Element.UNKNOWN, Direction.UNKNOWN),
            item=(Element.UNKNOWN, Direction.UNKNOWN),
            monster=(Element.UNKNOWN, Direction.UNKNOWN),
        )

    # Don't return a modified tile if no step is specified
    return tile, None

import cv2
import numpy

from common import Element, ImageProcessingStep

# We will have to revisit this logic to make sure we don't have false positives,
# but let's limit ourselves a few elements in the "Foundation" style for now:
# - Wall
# - Beethro
# - Conquer token
# - Floor
# This should be enough to solve mazes in that style


def classify_tile(tile, step=None):
    average_color = numpy.average(tile, (0, 1))
    if step == ImageProcessingStep.AVERAGE_TILE_COLOR:
        return [], numpy.ones(tile.shape) * average_color

    hsv_color = cv2.cvtColor(
        numpy.float32(numpy.ones((1, 1, 1)) * average_color), cv2.COLOR_RGB2HSV
    )
    hue = hsv_color[0, 0, 0]
    saturation = hsv_color[0, 0, 1]
    # If the saturation is low, it's probably empty floor
    if saturation < 0.1:
        elements = [Element.FLOOR]
    # Else, if the hue is purplish, it's probably a wall
    elif hue > 275 and hue < 300:
        elements = [Element.WALL]
    # Else, if the hue is yellowish, it's probably Beethro.
    elif hue > 33 and hue < 38:
        elements = [Element.FLOOR, Element.BEETHRO]
    # If it's a little more green, it's probably Beethro standing on a conquer token
    elif hue > 38 and hue < 42:
        elements = [Element.FLOOR, Element.TRIGGERED_CONQUER_TOKEN, Element.BEETHRO]
    # Else, if the hue is greenish, it's probably a conquer token
    elif hue > 110 and hue < 120:
        elements = [Element.FLOOR, Element.CONQUER_TOKEN]
    # If it's this other shade of green, it's probably a triggered conquer token
    elif hue > 95 and hue < 110:
        elements = [Element.FLOOR, Element.TRIGGERED_CONQUER_TOKEN]
    else:
        print(f"Found unknown tile with hue {hue} and saturation {saturation}")
        elements = [Element.UNKNOWN]
    if step == ImageProcessingStep.CLASSIFY_TILES:
        # Convert the tile to grayscale to make the text stand out.
        # We're converting it back to RGB so we can add the text, but
        # the tile will still look grayscale since we lose color information.
        modified_tile = cv2.cvtColor(
            cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2RGB
        )
        for element in elements:
            cv2.putText(
                modified_tile,
                element.value,
                (0, tile.shape[0]),
                cv2.FONT_HERSHEY_PLAIN,
                2,
                (255, 50, 0),
            )
        return elements, modified_tile

    # Don't return a modified tile if no step is specified
    return elements, None

import cv2
import numpy

from common import Entity, ImageProcessingStep

# We will have to revisit this logic to make sure we don't have false positives,
# but let's limit ourselves a few entities in the "Foundation" style for now:
# - Wall
# - Beethro
# - Victory token
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
        entities = [Entity.FLOOR]
    # Else, if the hue is purplish, it's probably a wall
    elif hue > 275 and hue < 295:
        entities = [Entity.WALL]
    # Else, if the hue is yellowish, it's probably Beethro
    elif hue > 30 and hue < 40:
        entities = [Entity.FLOOR, Entity.BEETHRO]
    # Else, if the hue is greenish, it's probably a victory token
    elif hue > 110 and hue < 120:
        entities = [Entity.FLOOR, Entity.VICTORY_TOKEN]
    else:
        entities = [Entity.UNKNOWN]
    if step == ImageProcessingStep.CLASSIFY_TILES:
        # Convert the tile to grayscale to make the text stand out.
        # We're converting it back to RGB so we can add the text, but
        # the tile will still look grayscale since we lose color information.
        modified_tile = cv2.cvtColor(
            cv2.cvtColor(tile, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2RGB
        )
        for entity in entities:
            cv2.putText(
                modified_tile,
                entity.value,
                (0, tile.shape[0]),
                cv2.FONT_HERSHEY_PLAIN,
                2,
                (255, 50, 0),
            )
        return entities, modified_tile

    # Don't return a modified tile if no step is specified
    return entities, None

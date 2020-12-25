import cv2
import numpy

from common import Entity, ImageProcessingStep

# We will have to revisit this logic to make sure we don't have false positives,
# but let's limit ourselves a few entities in the "Foundation" style for now:
# - Wall
# - Beethro
# - Victory token
# - (Floor)
# This should be enough to solve mazes in that style


def classify_tile(tile, step=None):
    average_color = numpy.average(tile, (0, 1))
    if step == ImageProcessingStep.AVERAGE_TILE_COLOR:
        return [], numpy.ones(tile.shape) * average_color

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

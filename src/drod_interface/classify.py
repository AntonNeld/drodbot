import cv2
from common import Entity, ImageProcessingStep

# We will have to revisit this logic to make sure we don't have false positives,
# but let's limit ourselves a few entities in the "Foundation" style for now:
# - Wall
# - Beethro
# - Victory token
# - (Floor)
# This should be enough to solve mazes in that style


def classify_tile(tile, step=None):
    entities = [Entity.UNKNOWN]
    if step == ImageProcessingStep.CLASSIFY_TILES:
        modified_tile = tile.copy()
        for entity in entities:
            cv2.putText(
                modified_tile,
                entity.value,
                (0, tile.shape[0]),
                cv2.FONT_HERSHEY_PLAIN,
                2,
                (0, 0, 0),
            )
        return entities, modified_tile

    # Don't return a modified tile if no step is specified
    return entities, None

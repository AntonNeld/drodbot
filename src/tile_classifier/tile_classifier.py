import os
import os.path

import numpy
import PIL

from common import (
    TILE_SIZE,
)
from room_simulator import ElementType, Direction
from .apparent_tile import ApparentTile
from util import find_color, element_layer


class TileClassifier:
    """This is used to determine the content of tiles."""

    def __init__(self):
        self._tile_data = None
        self._tile_examples = None

    def load_tile_data(self, tile_data_dir):
        """Load tile reference images.

        This needs to be done before we can classify anything.
        This method can be called again to reload the images.

        The image files should each contain one element, and be
        annotated with which element it is and which direction it has.

        Parameters
        ----------
        tile_data_dir
            The directory to read images from.
        """
        try:
            file_names = sorted(os.listdir(tile_data_dir))
            tile_data = []
            tile_examples = {}
            for file_name in file_names:
                image = PIL.Image.open(os.path.join(tile_data_dir, file_name))
                image_array = numpy.array(image)
                mask = numpy.logical_not(
                    numpy.logical_or(
                        find_color(image_array, (255, 0, 255)),  # Background
                        find_color(image_array, (192, 0, 192)),  # Shadow
                    )
                )
                element = getattr(ElementType, image.info["element"])

                direction = getattr(Direction, image.info["direction"])
                tile_data.append(
                    {
                        "file_name": file_name,
                        "image": _preprocess_image(image_array.astype(float)),
                        "mask": mask,
                        "element": element,
                        "direction": direction,
                        "layer": element_layer(element),
                    }
                )
                if (element, direction) not in tile_examples:
                    tile_examples[(element, direction)] = {
                        "image": image_array,
                        "mask": mask,
                    }
            self._tile_data = tile_data
            self._tile_examples = tile_examples
        except FileNotFoundError:
            print(
                f"No directory '{tile_data_dir}' found. "
                "You need to generate tile data before you can classify tiles."
            )

    def get_tile_image(self, apparent_tile):
        """Construct an image of an apparent tile.

        Parameters
        ----------
        apparent_tile
            The apparent tile.

        Returns
        -------
        An image that is similar to what the tile would look like.
        """
        tile_image = numpy.zeros((TILE_SIZE, TILE_SIZE, 3), dtype=numpy.uint8)
        for element, direction in [
            apparent_tile.room_piece,
            apparent_tile.floor_control,
            apparent_tile.checkpoint,
            apparent_tile.item,
            apparent_tile.monster,
        ]:
            if element == ElementType.NOTHING:
                continue
            image = self._tile_examples[(element, direction)]["image"]
            mask = self._tile_examples[(element, direction)]["mask"]
            tile_image[mask] = image[mask]
        return tile_image

    def classify_tiles(self, tiles, minimap_colors, return_debug_images=False):
        """Classify the given tiles.

        Parameters
        ----------
        tiles
            A dict with tile images as the values.
        minimap_colors
            A dict with the same keys as `tiles` and (r, g, b) color tuples
            as the values.
        return_debug_images
            If True, return a second dict with the same keys, and the values lists of
            (name, image) tuples with intermediate images.

        Returns
        -------
        A dict with the same keys as `tiles`, but ApparentTile objects
        representing the tile contents as the values. If `return_debug_images`
        is True, return a second dict with debug images.
        """
        if self._tile_data is None:
            raise RuntimeError("No tile data loaded, cannot classify tiles")
        classified_tiles = {
            key: ApparentTile(
                room_piece=(ElementType.UNKNOWN, Direction.NONE),
                floor_control=(ElementType.UNKNOWN, Direction.NONE),
                checkpoint=(ElementType.UNKNOWN, Direction.NONE),
                item=(ElementType.UNKNOWN, Direction.NONE),
                monster=(ElementType.UNKNOWN, Direction.NONE),
            )
            for key in tiles
        }
        debug_images = {key: [] for key in tiles}
        all_alternative_images = numpy.stack(
            [a["image"] for a in self._tile_data], axis=-1
        )
        all_alternative_masks = numpy.stack(
            [a["mask"] for a in self._tile_data], axis=-1
        )
        for key, image in tiles.items():
            if return_debug_images:
                processed_image, preprocess_debug_images = _preprocess_image(
                    image.astype(float), return_debug_images=True
                )
                debug_images[key].extend(preprocess_debug_images)
            else:
                processed_image = _preprocess_image(image.astype(float))

            minimap_filtered_indices, alternatives = zip(
                *[
                    (i, a)
                    for i, a in enumerate(self._tile_data)
                    if _compatible_with_minimap_color(
                        a["element"], a["layer"], minimap_colors[key]
                    )
                ]
            )
            alternative_images = all_alternative_images[
                :, :, :, minimap_filtered_indices
            ]
            alternative_masks = all_alternative_masks[:, :, minimap_filtered_indices]
            unmasked_image_diffs = numpy.sqrt(
                numpy.sum(
                    (processed_image[:, :, :, numpy.newaxis] - alternative_images) ** 2,
                    axis=2,
                )
            )
            found_elements_mask = numpy.ones((TILE_SIZE, TILE_SIZE), dtype=bool)
            passes = 1
            while numpy.sum(found_elements_mask) != 0:
                masks = numpy.logical_and(
                    alternative_masks, found_elements_mask[:, :, numpy.newaxis]
                )
                mask_sizes = numpy.sum(masks, axis=(0, 1))

                alternative_indices = [
                    i
                    for i, a in enumerate(alternatives)
                    if (
                        (
                            a["layer"] == "swords"
                            and classified_tiles[key].monster
                            == (ElementType.UNKNOWN, Direction.NONE)
                        )
                        or (
                            a["layer"] != "swords"
                            and getattr(classified_tiles[key], a["layer"])
                            == (ElementType.UNKNOWN, Direction.NONE)
                        )
                    )
                    and mask_sizes[i] != 0
                ]
                diffs = unmasked_image_diffs[:, :, alternative_indices]
                masked_diffs = diffs * masks[:, :, alternative_indices]
                average_diffs = (
                    numpy.sum(masked_diffs, axis=(0, 1))
                    / mask_sizes[alternative_indices]
                )
                if return_debug_images:
                    for index, alternative in enumerate(alternatives):
                        if index in alternative_indices:
                            true_index = alternative_indices.index(index)
                            try:
                                average_diff = int(average_diffs[true_index])
                            except ValueError:
                                average_diff = average_diffs[true_index]
                            identifier = alternative["file_name"].replace(".png", "")
                            debug_images[key].append(
                                (
                                    f"Pass {passes}: {identifier} ({average_diff})",
                                    masked_diffs[:, :, true_index],
                                )
                            )
                best_match_index, best_match_diff = min(
                    ((i, v) for (i, v) in enumerate(average_diffs)),
                    key=lambda x: x[1],
                )

                actual_index = alternative_indices[best_match_index]
                element = alternatives[actual_index]["element"]
                direction = alternatives[actual_index]["direction"]
                identifier = alternatives[actual_index]["file_name"].replace(".png", "")
                debug_images[key].append(
                    (
                        f"=Pass {passes}, selected " f"{identifier}=",
                        alternatives[actual_index]["image"],
                    )
                )
                element_mask = alternatives[actual_index]["mask"]
                found_elements_mask = numpy.logical_and(
                    found_elements_mask, numpy.logical_not(element_mask)
                )
                passes += 1
                layer = alternatives[actual_index]["layer"]
                if layer != "swords":  # Discard swords
                    layers = [
                        "monster",
                        "item",
                        "checkpoint",
                        "floor_control",
                        "room_piece",
                    ]
                    if getattr(classified_tiles[key], layer) != (
                        ElementType.UNKNOWN,
                        Direction.NONE,
                    ):
                        raise RuntimeError(
                            f"Saw {(element,direction)} in tile {key}, but it already "
                            f"has {getattr(classified_tiles[key],layer)} in "
                            f"the {layer} layer"
                        )
                    setattr(classified_tiles[key], layer, (element, direction))
                    for layer_above in layers[: layers.index(layer)]:
                        if getattr(classified_tiles[key], layer_above) == (
                            ElementType.UNKNOWN,
                            Direction.NONE,
                        ):
                            setattr(
                                classified_tiles[key],
                                layer_above,
                                (ElementType.NOTHING, Direction.NONE),
                            )
            # Assume there is nothing below an obstacle. Unless it's a tunnel, it
            # doesn't matter anyway. The classifier easily gets confused about what
            # is under obstacles, because of the shadows.
            if classified_tiles[key].item == (
                ElementType.OBSTACLE,
                Direction.NONE,
            ):
                classified_tiles[key].checkpoint = (
                    ElementType.NOTHING,
                    Direction.NONE,
                )
                classified_tiles[key].floor_control = (
                    ElementType.NOTHING,
                    Direction.NONE,
                )
                classified_tiles[key].room_piece = (
                    ElementType.FLOOR,
                    Direction.NONE,
                )
            # Open master walls are tricky because they can have several different
            # appearances, and are closed when playtesting. If we know there is a
            # master wall in a tile (because of the minimap), let's assume there is
            # nothing else there (except possibly Beethro).
            if classified_tiles[key].room_piece == (
                ElementType.MASTER_WALL,
                Direction.NONE,
            ):
                classified_tiles[key].floor_control = (
                    ElementType.NOTHING,
                    Direction.NONE,
                )
                classified_tiles[key].checkpoint = (
                    ElementType.NOTHING,
                    Direction.NONE,
                )
                classified_tiles[key].item = (ElementType.NOTHING, Direction.NONE)
                if classified_tiles[key].monster[0] != ElementType.BEETHRO:
                    classified_tiles[key].monster = (
                        ElementType.NOTHING,
                        Direction.NONE,
                    )

        if return_debug_images:
            return classified_tiles, debug_images
        return classified_tiles


def _preprocess_image(image, return_debug_images=False):
    """Pre-process an image before comparing it to others.

    This should be done both to input images when classifying,
    and tile data images when importing. This function currently
    does nothing, but is kept to make it easier to experiment.

    Parameters
    ----------
    image
        Image to process, with floats.
    return_debug_images
        If true, also return a list of (name, image) tuples with
        intermediate images.

    Returns
    -------
    The processed image, and optionally debug images.
    """
    if return_debug_images:
        return image, []
    return image


def _compatible_with_minimap_color(element, layer, color):
    """Check whether an element can be in a tile with the given color.

    Parameters
    ----------
    element
        The element to check.
    layer
        Which layer the element is in.
    color
        The color of the minimap in that location.

    Returns
    -------
    Whether the element can be in that place.
    """
    if layer == "item":
        if color != (128, 128, 128):
            # If there were an obstacle here, the color would be gray
            return element != ElementType.OBSTACLE
        # TODO: Same reasoning (but different color) holds for bombs
    if layer == "room_piece":
        if color == (0, 0, 0):
            # TODO: This can be broken or secret walls too
            return element == ElementType.WALL
        if color == (0, 0, 128):
            return element == ElementType.PIT
        if color == (255, 128, 0):
            # TODO: This can be hold complete walls or hot tiles too
            return element == ElementType.MASTER_WALL
        if color == (255, 255, 0):
            return element == ElementType.YELLOW_DOOR
        if color == (255, 255, 164):
            return element == ElementType.YELLOW_DOOR_OPEN
        if color == (0, 255, 0):
            return element == ElementType.GREEN_DOOR
        if color == (128, 255, 128):  # Open green door, or recently cleared room
            # TODO: This can be oremites too. They are not the same color, but
            # they disappear from the minimap when the room is just cleared.
            return element in [
                ElementType.FLOOR,
                ElementType.GREEN_DOOR_OPEN,
            ]
        if color == (0, 255, 255):
            return element == ElementType.BLUE_DOOR
        if color == (164, 255, 255):
            return element == ElementType.BLUE_DOOR_OPEN
        if color == (210, 210, 100):
            return element == ElementType.STAIRS
        if color == (255, 200, 200):
            # This only appears in the editor, but we may as well have it
            return element == ElementType.FLOOR
        if color == (255, 0, 0):  # Not cleared, required room
            # TODO: This can be red doors too
            return element == ElementType.FLOOR
        if color == (255, 0, 255):  # Not cleared, not required room
            return element == ElementType.FLOOR
        if color == (229, 229, 229):  # Cleared room, revisited
            return element == ElementType.FLOOR
        if color == (128, 128, 128):
            # This could be an obstacle, so there may be anything below it.
            # But it doesn't actually matter unless it's a tunnel, so let's
            # say it's either a tunnel or a floor.
            # TODO: It could also be a tunnel
            return element == ElementType.FLOOR
        print(f"Unknown minimap color {color}")
    return True

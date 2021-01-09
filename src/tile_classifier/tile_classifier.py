import os
import os.path

import numpy
import PIL

from common import (
    TILE_SIZE,
    Element,
    ROOM_PIECES,
    FLOOR_CONTROLS,
    CHECKPOINTS,
    ITEMS,
    MONSTERS,
    Direction,
    Tile,
)
from util import find_color


class TileClassifier:
    """This is used to determine the content of tiles."""

    def __init__(self):
        self._tile_data = None

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
            for file_name in file_names:
                image = PIL.Image.open(os.path.join(tile_data_dir, file_name))
                image_array = numpy.array(image)
                element = next(e for e in Element if e.value == image.info["element"])
                direction = next(
                    d for d in Direction if d.value == image.info["direction"]
                )
                tile_data.append(
                    {
                        "file_name": file_name,
                        "image": _preprocess_image(image_array.astype(float)),
                        "mask": numpy.logical_not(
                            numpy.logical_or(
                                find_color(image_array, (255, 0, 255)),  # Background
                                find_color(image_array, (192, 0, 192)),  # Shadow
                            )
                        ),
                        "element": element,
                        "direction": direction,
                        "layer": "monster"
                        if element in MONSTERS
                        else "item"
                        if element in ITEMS
                        else "checkpoint"
                        if element in CHECKPOINTS
                        else "floor_control"
                        if element in FLOOR_CONTROLS
                        else "room_piece"
                        if element in ROOM_PIECES
                        else "swords",
                    }
                )
            self._tile_data = tile_data
        except FileNotFoundError:
            print(
                f"No directory '{self._tile_data_dir}' found. "
                "You need to generate tile data before you can classify tiles."
            )

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
        A dict with the same keys as `tiles`, but Tile objects
        representing the tile contents as the values. If `return_debug_images`
        is True, return a second dict with debug images.
        """
        if self._tile_data is None:
            raise RuntimeError("No tile data loaded, cannot classify tiles")
        classified_tiles = {
            key: Tile(
                room_piece=(Element.UNKNOWN, Direction.UNKNOWN),
                floor_control=(Element.UNKNOWN, Direction.UNKNOWN),
                checkpoint=(Element.UNKNOWN, Direction.UNKNOWN),
                item=(Element.UNKNOWN, Direction.UNKNOWN),
                monster=(Element.UNKNOWN, Direction.UNKNOWN),
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
                            == (Element.UNKNOWN, Direction.UNKNOWN)
                        )
                        or (
                            a["layer"] != "swords"
                            and getattr(classified_tiles[key], a["layer"])
                            == (Element.UNKNOWN, Direction.UNKNOWN)
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
                        Element.UNKNOWN,
                        Direction.UNKNOWN,
                    ):
                        raise RuntimeError(
                            f"Saw {(element,direction)} in tile {key}, but it already "
                            f"has {getattr(classified_tiles[key],layer)} in "
                            f"the {layer} layer"
                        )
                    setattr(classified_tiles[key], layer, (element, direction))
                    for layer_above in layers[: layers.index(layer)]:
                        if getattr(classified_tiles[key], layer_above) == (
                            Element.UNKNOWN,
                            Direction.UNKNOWN,
                        ):
                            setattr(
                                classified_tiles[key],
                                layer_above,
                                (Element.NOTHING, Direction.NONE),
                            )
            # Assume there is nothing below an obstacle. Unless it's a tunnel, it
            # doesn't matter anyway. The classifier easily gets confused about what
            # is under obstacles, because of the shadows.
            if classified_tiles[key].item == (Element.OBSTACLE, Direction.NONE):
                classified_tiles[key].checkpoint = (Element.NOTHING, Direction.NONE)
                classified_tiles[key].floor_control = (Element.NOTHING, Direction.NONE)
                classified_tiles[key].room_piece = (Element.FLOOR, Direction.NONE)
            # Open master walls are tricky because they can have several different
            # appearances, and are closed when playtesting. If we know there is a
            # master wall in a tile (because of the minimap), let's assume there is
            # nothing else there (except possibly Beethro).
            if classified_tiles[key].room_piece == (
                Element.MASTER_WALL,
                Direction.NONE,
            ):
                classified_tiles[key].floor_control = (Element.NOTHING, Direction.NONE)
                classified_tiles[key].checkpoint = (Element.NOTHING, Direction.NONE)
                classified_tiles[key].item = (Element.NOTHING, Direction.NONE)
                if classified_tiles[key].monster[0] != Element.BEETHRO:
                    classified_tiles[key].monster = (Element.NOTHING, Direction.NONE)

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
            return element != Element.OBSTACLE
        # TODO: Same reasoning (but different color) holds for bombs
    if layer == "room_piece":
        if color == (0, 0, 0):
            # TODO: This can be broken or secret walls too
            return element == Element.WALL
        if color == (0, 0, 128):
            return element == Element.PIT
        if color == (255, 128, 0):
            # TODO: This can be hold complete walls or hot tiles too
            return element == Element.MASTER_WALL
        if color == (255, 255, 0):
            return element == Element.YELLOW_DOOR
        if color == (255, 255, 164):
            return element == Element.YELLOW_DOOR_OPEN
        if color == (0, 255, 0):
            return element == Element.GREEN_DOOR
        if color == (128, 255, 128):  # Open green door, or recently cleared room
            # TODO: This can be oremites too. They are not the same color, but
            # they disappear from the minimap when the room is just cleared.
            return element in [Element.FLOOR, Element.GREEN_DOOR_OPEN]
        if color == (0, 255, 255):
            return element == Element.BLUE_DOOR
        if color == (164, 255, 255):
            return element == Element.BLUE_DOOR_OPEN
        if color == (210, 210, 100):
            return element == Element.STAIRS
        if color == (255, 200, 200):
            # This only appears in the editor, but we may as well have it
            return element == Element.FLOOR
        if color == (255, 0, 0):  # Not cleared, required room
            # TODO: This can be red doors too
            return element == Element.FLOOR
        if color == (255, 0, 255):  # Not cleared, not required room
            return element == Element.FLOOR
        if color == (229, 229, 229):  # Cleared room, revisited
            return element == Element.FLOOR
        if color == (128, 128, 128):
            # This could be an obstacle, so there may be anything below it.
            # But it doesn't actually matter unless it's a tunnel, so let's
            # say it's either a tunnel or a floor.
            # TODO: It could also be a tunnel
            return element == Element.FLOOR
        print(f"Unknown minimap color {color}")
    return True

import os
import os.path

import numpy
import PIL

from common import (
    ROOM_HEIGHT_IN_TILES,
    ROOM_WIDTH_IN_TILES,
    TILE_SIZE,
)
from room_simulator import ElementType, Direction
from .apparent_tile import ApparentTile
from util import find_color, element_layer

_SHADABLE_ELEMENTS = set(
    [
        ElementType.GREEN_DOOR_OPEN,
        ElementType.RED_DOOR_OPEN,
        ElementType.BLUE_DOOR_OPEN,
        ElementType.YELLOW_DOOR_OPEN,
        ElementType.FLOOR,
        ElementType.TRAPDOOR,
        ElementType.FORCE_ARROW,
        ElementType.CHECKPOINT,
        ElementType.ORB,
        ElementType.SCROLL,
        ElementType.MIMIC_POTION,
        ElementType.INVISIBILITY_POTION,
        ElementType.OBSTACLE,
        ElementType.CONQUER_TOKEN,
    ]
)


class TileClassifier:
    """This is used to determine the content of tiles."""

    def __init__(self):
        self._non_positional_non_styled_tile_data = None
        self._non_positional_non_styled_alternative_images = None
        self._non_positional_non_styled_alternative_masks = None
        self._non_positional_styled_tile_data = None
        self._non_positional_styled_alternative_images = None
        self._non_positional_styled_alternative_masks = None
        self._positional_styled_tile_data = None
        self._positional_styled_alternative_images = None
        self._positional_styled_alternative_masks = None
        self._textures = None
        self._shadows = None
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
            # Load individual tiles
            file_names = sorted(os.listdir(os.path.join(tile_data_dir, "tiles")))
            non_positional_non_styled_tile_data = []
            non_positional_styled_tile_data = {}
            for file_name in file_names:
                image = PIL.Image.open(os.path.join(tile_data_dir, "tiles", file_name))
                image_array = numpy.array(image)
                mask = numpy.logical_not(
                    numpy.logical_or(
                        find_color(image_array, (255, 0, 255)),  # Background
                        find_color(image_array, (192, 0, 192)),  # Shadow
                    )
                )
                element = getattr(ElementType, image.info["element"])
                direction = getattr(Direction, image.info["direction"])
                if "room_style" not in image.info:
                    non_positional_non_styled_tile_data.append(
                        {
                            "file_name": file_name,
                            # Keeping image and mask here does not take up extra memory,
                            # probably because of some behind-the-scenes optimization
                            "image": _preprocess_image(image_array.astype(float)),
                            "mask": mask,
                            "element": element,
                            "direction": direction,
                            "layer": element_layer(element),
                        }
                    )
                else:
                    style = image.info["room_style"]
                    if style not in non_positional_styled_tile_data:
                        non_positional_styled_tile_data[style] = []
                    non_positional_styled_tile_data[style].append(
                        {
                            "file_name": file_name,
                            "image": _preprocess_image(image_array.astype(float)),
                            "mask": mask,
                            "element": element,
                            "direction": direction,
                            "layer": element_layer(element),
                        }
                    )

            # Load textures
            textures = []
            room_image_file_names = sorted(
                os.listdir(os.path.join(tile_data_dir, "textures"))
            )
            positional_styled_tile_data = {}
            for file_name in room_image_file_names:
                image = PIL.Image.open(
                    os.path.join(tile_data_dir, "textures", file_name)
                )
                image_array = numpy.array(image)
                element = getattr(ElementType, image.info["element"])
                room_style = image.info["room_style"]
                textures.append(
                    {
                        "file_name": file_name,
                        "image": image_array,
                        "element": element,
                        "room_style": room_style,
                    }
                )
                if room_style not in positional_styled_tile_data:
                    positional_styled_tile_data[room_style] = {}
                # Extend tile_data with images of all tiles
                texture_tiles = {}
                for x in range(ROOM_WIDTH_IN_TILES):
                    for y in range(ROOM_HEIGHT_IN_TILES):
                        if (x, y) not in positional_styled_tile_data[room_style]:
                            positional_styled_tile_data[room_style][(x, y)] = []
                        x_in_image = x % (image_array.shape[1] // TILE_SIZE)
                        y_in_image = y % (image_array.shape[0] // TILE_SIZE)
                        if (x_in_image, y_in_image) not in texture_tiles:
                            texture_tiles[(x_in_image, y_in_image)] = _preprocess_image(
                                image_array[
                                    y_in_image
                                    * TILE_SIZE : (y_in_image + 1)
                                    * TILE_SIZE,
                                    x_in_image
                                    * TILE_SIZE : (x_in_image + 1)
                                    * TILE_SIZE,
                                    :,
                                ].astype(float)
                            )
                        positional_styled_tile_data[room_style][(x, y)].append(
                            {
                                "file_name": file_name,
                                "image": texture_tiles[(x_in_image, y_in_image)],
                                "mask": numpy.ones((TILE_SIZE, TILE_SIZE), dtype=bool),
                                "element": element,
                                "direction": Direction.NONE,
                                "layer": "room_piece",
                                "position": (x, y),
                            }
                        )
            # Load shadows
            shadows = {}
            shadow_file_names = sorted(
                os.listdir(os.path.join(tile_data_dir, "shadows"))
            )
            for file_name in shadow_file_names:
                image = PIL.Image.open(
                    os.path.join(tile_data_dir, "shadows", file_name)
                )
                image_array = numpy.array(image)
                room_style = image.info["room_style"]
                if room_style not in shadows:
                    shadows[room_style] = []
                shadows[room_style].append(
                    {
                        "file_name": file_name,
                        "image": find_color(image_array, (192, 0, 192)),
                    }
                )

            # Create examples of tiles, for reconstructing a room image
            tile_examples = {}
            for tile_info in (
                non_positional_non_styled_tile_data
                + non_positional_styled_tile_data["Foundation"]
                + positional_styled_tile_data["Foundation"][(0, 0)]
            ):
                element = tile_info["element"]
                direction = tile_info["direction"]
                image_array = tile_info["image"]
                mask = tile_info["mask"]
                if (element, direction) not in tile_examples:
                    tile_examples[(element, direction)] = {
                        "image": image_array,
                        "mask": mask,
                    }

            self._textures = textures
            self._shadows = shadows
            self._non_positional_non_styled_tile_data = (
                non_positional_non_styled_tile_data
            )
            self._non_positional_styled_tile_data = non_positional_styled_tile_data
            self._positional_styled_tile_data = positional_styled_tile_data
            self._tile_examples = tile_examples
            # Pre-generate numpy arrays for performance
            self._non_positional_non_styled_alternative_images = numpy.stack(
                [a["image"] for a in non_positional_non_styled_tile_data], axis=-1
            )
            self._non_positional_non_styled_alternative_masks = numpy.stack(
                [a["mask"] for a in non_positional_non_styled_tile_data], axis=-1
            )
            self._non_positional_styled_alternative_images = {
                style: numpy.stack([a["image"] for a in data], axis=-1)
                for style, data in non_positional_styled_tile_data.items()
            }
            self._non_positional_styled_alternative_masks = {
                style: numpy.stack([a["mask"] for a in data], axis=-1)
                for (style, data) in non_positional_styled_tile_data.items()
            }
            self._positional_styled_alternative_images = {
                style: {
                    position: numpy.stack([a["image"] for a in data], axis=-1)
                    for (position, data) in positional_styled_tile_data[style].items()
                }
                for style in positional_styled_tile_data
            }
            self._positional_styled_alternative_masks = {
                style: {
                    position: numpy.stack([a["mask"] for a in data], axis=-1)
                    for (position, data) in positional_styled_tile_data[style].items()
                }
                for style in positional_styled_tile_data
            }

        except FileNotFoundError:
            print(
                "Not all tile data is present. "
                "You need to generate tile data before you can classify tiles."
            )

    def _get_alternatives(self, position, minimap_color, room_style, shadow=None):
        """Get the possible alternative tiles based on some conditions.

        Parameters
        ----------
        position
            The position.
        minimap_color
            The minimap color.
        room_style
            The room style, or None.
        shadow
            Add this shadow over elements that can be in the shade. Skip if None.

        Returns
        -------
        alternatives
            List of tile info for the possible tiles.
        alternative_images
            A numpy array with the alternative images.
            The last dimension matches the list of alternatives.
        alternative_masks
            A numpy array with the alternative masks.
            The last dimension matches the list of alternatives.
        """
        try:
            if room_style is not None:
                all_tile_data = (
                    self._non_positional_non_styled_tile_data
                    + self._non_positional_styled_tile_data[room_style]
                    + self._positional_styled_tile_data[room_style][position]
                )
                stacked_images = numpy.concatenate(
                    (
                        self._non_positional_non_styled_alternative_images,
                        self._non_positional_styled_alternative_images[room_style],
                        self._positional_styled_alternative_images[room_style][
                            position
                        ],
                    ),
                    axis=-1,
                )
                stacked_masks = numpy.concatenate(
                    (
                        self._non_positional_non_styled_alternative_masks,
                        self._non_positional_styled_alternative_masks[room_style],
                        self._positional_styled_alternative_masks[room_style][position],
                    ),
                    axis=-1,
                )
            else:
                raise RuntimeError(
                    "Interpreting room without detected style not implemented"
                )

            filtered_indices, alternatives = zip(
                *[
                    (i, a)
                    for i, a in enumerate(all_tile_data)
                    if _compatible_with_minimap_color(
                        a["element"], a["layer"], minimap_color
                    )
                ]
            )
        except ValueError:
            raise RuntimeError("No tile data loaded, cannot classify tiles")
        alternative_images = stacked_images[:, :, :, filtered_indices]
        alternative_masks = stacked_masks[:, :, filtered_indices]
        if shadow is not None:
            shadow_mask = shadow["image"]
            shadable_indices = [
                i
                for i, alternative in enumerate(alternatives)
                if alternative["element"] in _SHADABLE_ELEMENTS
            ]
            shaded = alternative_images[:, :, :, shadable_indices]
            shaded[shadow_mask, :, :] = shaded[shadow_mask, :, :] * 0.75
            alternative_images[:, :, :, shadable_indices] = shaded
        return alternatives, alternative_images, alternative_masks

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

    def get_easy_tiles(self, room_image, return_debug_images=False):
        """Get the easily classified tiles from a room image.

        Easily classified tiles are those that completely match a
        portion of one of the full-room images, i.e. tiles with only
        a floor, pit or (inside) wall.

        Parameters
        ----------
        room_image
            The room image.
        return_debug_images
            Whether to return debug images.

        Returns
        -------
        classified_tiles
            A dict mapping coordinates to ApparentTiles, with only classified tiles
            present.
        detected_style
            The detected room style.
        debug_images
            If return_debug_images is True, also return a list of debug images.
        """
        classified_tiles = {}
        if return_debug_images:
            debug_images = []
        detected_style = None
        for texture in self._textures:
            file_name = texture["file_name"]
            image = texture["image"]
            element = texture["element"]
            room_style = texture["room_style"]
            if detected_style is not None and room_style != detected_style:
                continue
            expanded_image = numpy.tile(
                image,
                (
                    ROOM_HEIGHT_IN_TILES * TILE_SIZE // image.shape[0] + 1,
                    ROOM_WIDTH_IN_TILES * TILE_SIZE // image.shape[1] + 1,
                    1,
                ),
            )[: ROOM_HEIGHT_IN_TILES * TILE_SIZE, : ROOM_WIDTH_IN_TILES * TILE_SIZE, :]
            # TODO: Have a mask for already found tiles for performance?
            matching_pixels = (expanded_image == room_image).all(axis=2)
            if return_debug_images:
                debug_images.append((f"Matching pixels {file_name}", matching_pixels))
            matching_tiles = numpy.zeros(
                (ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES), dtype=bool
            )
            # TODO: Could be done faster by remapping matching_pixels and mapping back?
            for x in range(ROOM_WIDTH_IN_TILES):
                for y in range(ROOM_HEIGHT_IN_TILES):
                    if matching_pixels[
                        # Only the lower 10 rows need to match. This helps with north
                        # edges of walls, where these pixels are part of the texture
                        y * TILE_SIZE + 12 : (y + 1) * TILE_SIZE,
                        x * TILE_SIZE : (x + 1) * TILE_SIZE,
                    ].all():
                        matching_tiles[y, x] = True
            if return_debug_images:
                debug_images.append((f"Matching tiles {file_name}", matching_tiles))
            if matching_tiles.any():
                detected_style = room_style
            for coords in numpy.argwhere(matching_tiles):
                position = (coords[1], coords[0])
                # Easy tiles are always room pieces
                classified_tiles[position] = ApparentTile(
                    room_piece=(element, Direction.NONE)
                )

        if detected_style is None:
            print("Did not detect a style from texture comparison")
        if return_debug_images:
            return classified_tiles, detected_style, debug_images
        return classified_tiles, detected_style

    def classify_tiles(
        self, tiles, minimap_colors, room_style=None, return_debug_images=False
    ):
        """Classify the given tiles.

        Parameters
        ----------
        tiles
            A dict with positions as keys and tile images as the values.
        minimap_colors
            A dict with the same keys as `tiles` and (r, g, b) color tuples
            as the values.
        room_style
            The room style, or None if not known. This narrows down the element images
            to compare with.
        return_debug_images
            If True, return a second dict with the same keys, and the values lists of
            (name, image) tuples with intermediate images.

        Returns
        -------
        classified_tiles
            A dict with the same keys as `tiles`, but ApparentTile objects
            representing the tile contents as the values.
        difficult_tiles
            A list of all positions which were difficult to interpret.
        debug_images
            If `return_debug_images` is True, return another dict with debug images.
        """
        classified_tiles = {}
        debug_images = {key: [] for key in tiles}
        difficult_tiles = []
        for key, image in tiles.items():
            if return_debug_images:
                preprocessed_image, preprocess_debug_images = _preprocess_image(
                    image.astype(float), return_debug_images=True
                )
                debug_images[key].extend(preprocess_debug_images)
            else:
                preprocessed_image = _preprocess_image(image.astype(float))

            min_max_min_diff = None
            for shadow in [None, *self._shadows[room_style]]:
                if return_debug_images:
                    (
                        new_tile,
                        max_min_diff,
                        classified_debug_images,
                    ) = self._classify_tile(
                        preprocessed_image,
                        key,
                        minimap_colors[key],
                        room_style,
                        shadow=shadow,
                        return_debug_images=True,
                    )
                else:
                    new_tile, max_min_diff = self._classify_tile(
                        preprocessed_image,
                        key,
                        minimap_colors[key],
                        room_style,
                        shadow=shadow,
                    )
                if min_max_min_diff is None or max_min_diff < min_max_min_diff:
                    min_max_min_diff = max_min_diff
                    tile = new_tile
                if min_max_min_diff < 30:
                    break
            if (
                min_max_min_diff >= 30 and tile.item[0] != ElementType.OBSTACLE
            ):  # Obstacles are always difficult, that's not news
                difficult_tiles.append(key)
            if return_debug_images:
                debug_images[key].extend(classified_debug_images)

            # Assume there is nothing below an obstacle. Unless it's a tunnel, it
            # doesn't matter anyway. The classifier easily gets confused about what
            # is under obstacles, because of the shadows.
            if tile.item == (
                ElementType.OBSTACLE,
                Direction.NONE,
            ):
                tile.checkpoint = (
                    ElementType.NOTHING,
                    Direction.NONE,
                )
                tile.floor_control = (
                    ElementType.NOTHING,
                    Direction.NONE,
                )
                tile.room_piece = (
                    ElementType.FLOOR,
                    Direction.NONE,
                )
            # Open master walls are tricky because they can have several different
            # appearances, and are closed when playtesting. If we know there is a
            # master wall in a tile (because of the minimap), let's assume there is
            # nothing else there (except possibly Beethro).
            if tile.room_piece == (
                ElementType.MASTER_WALL,
                Direction.NONE,
            ):
                tile.floor_control = (
                    ElementType.NOTHING,
                    Direction.NONE,
                )
                tile.checkpoint = (
                    ElementType.NOTHING,
                    Direction.NONE,
                )
                tile.item = (ElementType.NOTHING, Direction.NONE)
                if tile.monster[0] != ElementType.BEETHRO:
                    tile.monster = (
                        ElementType.NOTHING,
                        Direction.NONE,
                    )
            classified_tiles[key] = tile

        if return_debug_images:
            return classified_tiles, difficult_tiles, debug_images
        return classified_tiles, difficult_tiles

    def _classify_tile(
        self,
        preprocessed_image,
        position,
        minimap_color,
        room_style,
        shadow=None,
        return_debug_images=False,
    ):
        """Classify a single tile.

        Parameters
        ----------
        preprocessed_image
            The tile image, already preprocessed.
        position
            The position of the tile. Used to get the correct part of textures.
        minimap_color
            The color of the minimap at the position. Used to narrow down alternatives.
        room_style
            The room style. Used to compare to the correct images.
        shadow
            Shade elements that can be in the shade using this shadow. Skip if None.
        return_debug_images
            Whether to also return debug images.

        Returns
        -------
        tile
            An ApparentTile with the contents of the tile.
        max_min_diff
            The maximum average diff between the selected tile and the chosen element.
            Bigger means the classification is more uncertain.
        debug_images
            Debug images. Only returned if return_debug_images is True.
        """
        if return_debug_images:
            debug_images = []
        tile = ApparentTile(
            room_piece=(ElementType.UNKNOWN, Direction.NONE),
            floor_control=(ElementType.UNKNOWN, Direction.NONE),
            checkpoint=(ElementType.UNKNOWN, Direction.NONE),
            item=(ElementType.UNKNOWN, Direction.NONE),
            monster=(ElementType.UNKNOWN, Direction.NONE),
        )

        alternatives, alternative_images, alternative_masks = self._get_alternatives(
            position, minimap_color, room_style, shadow=shadow
        )
        unmasked_image_diffs = numpy.sqrt(
            numpy.sum(
                (preprocessed_image[:, :, :, numpy.newaxis] - alternative_images) ** 2,
                axis=2,
            )
        )
        found_elements_mask = numpy.ones((TILE_SIZE, TILE_SIZE), dtype=bool)
        passes = 1
        max_min_diff = 0
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
                        and tile.monster == (ElementType.UNKNOWN, Direction.NONE)
                    )
                    or (
                        a["layer"] != "swords"
                        and getattr(tile, a["layer"])
                        == (ElementType.UNKNOWN, Direction.NONE)
                    )
                )
                and mask_sizes[i] != 0
            ]
            diffs = unmasked_image_diffs[:, :, alternative_indices]
            masked_diffs = diffs * masks[:, :, alternative_indices]
            average_diffs = (
                numpy.sum(masked_diffs, axis=(0, 1)) / mask_sizes[alternative_indices]
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
                        if shadow is not None:
                            shadow_index = (
                                shadow["file_name"].split("_")[-1].replace(".png", "")
                            )
                            identifier = f"{identifier}+shdw{shadow_index}"
                        debug_images.append(
                            (
                                f"Pass {passes}: {identifier} ({average_diff})",
                                masked_diffs[:, :, true_index],
                            )
                        )
            best_match_index, min_diff = min(
                ((i, v) for (i, v) in enumerate(average_diffs)),
                key=lambda x: x[1],
            )
            if min_diff > max_min_diff:
                max_min_diff = min_diff

            actual_index = alternative_indices[best_match_index]
            element = alternatives[actual_index]["element"]
            direction = alternatives[actual_index]["direction"]
            identifier = alternatives[actual_index]["file_name"].replace(".png", "")
            if shadow is not None:
                shadow_index = shadow["file_name"].split("_")[-1].replace(".png", "")
                identifier = f"{identifier}+shdw{shadow_index}"
            if return_debug_images:
                debug_images.append(
                    (
                        f"=Pass {passes}, selected " f"{identifier}=",
                        alternative_images[:, :, :, actual_index],
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
                if getattr(tile, layer) != (
                    ElementType.UNKNOWN,
                    Direction.NONE,
                ):
                    raise RuntimeError(
                        f"Saw {(element,direction)} in tile {position}, but it already "
                        f"has {getattr(tile,layer)} in "
                        f"the {layer} layer"
                    )
                setattr(tile, layer, (element, direction))
                for layer_above in layers[: layers.index(layer)]:
                    if getattr(tile, layer_above) == (
                        ElementType.UNKNOWN,
                        Direction.NONE,
                    ):
                        setattr(
                            tile,
                            layer_above,
                            (ElementType.NOTHING, Direction.NONE),
                        )
        if return_debug_images:
            return tile, max_min_diff, debug_images
        return tile, max_min_diff


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
            return element in [ElementType.BLUE_DOOR, ElementType.BLUE_DOOR_OPEN]
        if color == (164, 255, 255):
            return element in [ElementType.BLUE_DOOR, ElementType.BLUE_DOOR_OPEN]
        if color == (255, 64, 64):
            return element == ElementType.RED_DOOR_OPEN
        if color == (255, 128, 128):
            return element == ElementType.TRAPDOOR
        if color == (210, 210, 100):
            return element == ElementType.STAIRS
        if color == (255, 200, 200):
            # This only appears in the editor, but we may as well have it
            return element == ElementType.FLOOR
        if color == (255, 0, 0):  # Red door or not cleared, required room
            return element in [ElementType.FLOOR, ElementType.RED_DOOR]
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

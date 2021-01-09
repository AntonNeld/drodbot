import json
import os
import os.path
import shutil

import numpy
import PIL
from PIL.PngImagePlugin import PngInfo

from common import (
    TILE_SIZE,
    GUIEvent,
    Element,
    ROOM_PIECES,
    FLOOR_CONTROLS,
    CHECKPOINTS,
    ITEMS,
    MONSTERS,
    Direction,
    Room,
    Tile,
)
from util import find_color
from .editor_utils import (
    place_fully_directional_elements,
    place_nondirectional_edges_elements,
    place_rectangle,
    place_sized_obstacles,
    place_sworded_element,
)


class ComparisonTileClassifier:
    def __init__(self, tile_data_dir, sample_data_dir, editor_interface, window_queue):
        self._tile_data_dir = tile_data_dir
        self._sample_data_dir = sample_data_dir
        self._interface = editor_interface
        self._sample_data = []
        self._queue = window_queue
        self._tile_data = self._load_tile_data()

    def _load_tile_data(self):
        try:
            file_names = sorted(os.listdir(self._tile_data_dir))
            tile_data = []
            for file_name in file_names:
                image = PIL.Image.open(os.path.join(self._tile_data_dir, file_name))
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
            return tile_data
        except FileNotFoundError:
            print(
                f"No directory '{self._tile_data_dir}' found. "
                "You need to generate tile data before you can classify tiles."
            )
            return None

    async def load_sample_data(self):
        """Load the sample data and send it to the GUI."""
        print("Loading sample data...")
        self._sample_data = []
        try:
            file_names = os.listdir(self._sample_data_dir)
        except FileNotFoundError:
            print("No sample data directory found")
            self._queue.put((GUIEvent.SET_TRAINING_DATA, self._sample_data))
            return
        for file_name in file_names:
            image = PIL.Image.open(os.path.join(self._sample_data_dir, file_name))
            content = Tile.from_json(image.info["tile_json"])
            minimap_color = tuple(json.loads(image.info["minimap_color"]))
            self._sample_data.append(
                {
                    "image": numpy.array(image),
                    "real_content": content,
                    "file_name": file_name,
                    "minimap_color": minimap_color,
                }
            )
        print("Classifying sample data...")
        self._classify_sample_data()
        self._queue.put((GUIEvent.SET_TRAINING_DATA, self._sample_data))
        print("Loaded and classified sample data")

    async def generate_tile_data(self):
        """Get tile data using the editor.

        This must be done before the classifier will work.
        """
        print("Getting tile data...")
        await self._interface.initialize()
        await self._interface.clear_room()
        await self._interface.set_floor_image(
            os.path.dirname(os.path.realpath(__file__)), "background"
        )
        await self._interface.place_element(
            Element.FLOOR, Direction.NONE, (0, 0), (37, 31), style="image"
        )

        elements = (
            await place_sworded_element(
                self._interface, Element.BEETHRO, Element.BEETHRO_SWORD, 0, 0
            )
            + await place_fully_directional_elements(
                self._interface, Element.ROACH, 0, 3
            )
            + await place_fully_directional_elements(
                self._interface, Element.FORCE_ARROW, 8, 2
            )
            + await place_nondirectional_edges_elements(
                self._interface, Element.WALL, 1, 4, "hard"
            )
            + await place_nondirectional_edges_elements(
                self._interface, Element.YELLOW_DOOR, 1, 9
            )
            + await place_nondirectional_edges_elements(
                self._interface, Element.BLUE_DOOR, 1, 14
            )
            + await place_nondirectional_edges_elements(
                self._interface, Element.GREEN_DOOR, 1, 19
            )
            + await place_nondirectional_edges_elements(
                self._interface, Element.YELLOW_DOOR_OPEN, 11, 9
            )
            + await place_nondirectional_edges_elements(
                self._interface, Element.BLUE_DOOR_OPEN, 11, 14
            )
            + await place_nondirectional_edges_elements(
                self._interface, Element.GREEN_DOOR_OPEN, 11, 19
            )
            + await place_sized_obstacles(self._interface, "rock_1", 7, 0, [1, 2, 3])
            + await place_sized_obstacles(self._interface, "rock_2", 11, 4, [1, 2, 3])
            + await place_sized_obstacles(
                self._interface, "square_statue", 16, 1, [1, 2, 4]
            )
            + await place_rectangle(
                self._interface, Element.WALL, 20, 5, 9, 9, include_all_sides=False
            )
            # Place some force arrows in the shadow, since we're having trouble seeing
            # those otherwise
            + await place_fully_directional_elements(
                self._interface, Element.FORCE_ARROW, 21, 14, one_line=True
            )
            + await place_rectangle(self._interface, Element.PIT, 20, 15, 9, 9)
            + await place_rectangle(
                self._interface, Element.FLOOR, 30, 5, 4, 4, style="mosaic"
            )
            + await place_rectangle(
                self._interface, Element.FLOOR, 30, 9, 4, 4, style="road"
            )
            + await place_rectangle(
                self._interface, Element.FLOOR, 30, 13, 4, 4, style="grass"
            )
            + await place_rectangle(
                self._interface, Element.FLOOR, 30, 17, 4, 4, style="dirt"
            )
            + await place_rectangle(
                self._interface, Element.FLOOR, 30, 21, 4, 4, style="alternate"
            )
            + await place_rectangle(self._interface, Element.STAIRS, 34, 5, 1, 19)
            + await place_rectangle(
                self._interface, Element.STAIRS, 35, 5, 1, 19, style="up"
            )
        )
        extra_elements = [
            (Element.FLOOR, Direction.NONE, 2, 2, "normal"),
            (Element.FLOOR, Direction.NONE, 3, 2, "normal"),
            (Element.CONQUER_TOKEN, Direction.NONE, 0, 5, None),
            (Element.MASTER_WALL, Direction.NONE, 4, 3, None),
            (Element.ORB, Direction.NONE, 6, 1, None),
            (Element.CHECKPOINT, Direction.NONE, 7, 1, None),
            (Element.SCROLL, Direction.NONE, 12, 3, None),
        ]
        for (element, direction, x, y, style) in extra_elements:
            await self._interface.place_element(element, direction, (x, y), style=style)
        elements.extend(extra_elements)

        await self._interface.start_test_room((37, 31), Direction.SE)
        tiles, _ = await self._interface.get_tiles_and_colors()
        await self._interface.stop_test_room()
        if os.path.exists(self._tile_data_dir):
            shutil.rmtree(self._tile_data_dir)
        os.makedirs(self._tile_data_dir)
        used_names = []
        for (element, direction, x, y, style) in elements:
            png_info = PngInfo()
            png_info.add_text("element", element.value)
            png_info.add_text("direction", direction.value)
            image = PIL.Image.fromarray(tiles[(x, y)])
            direction_str = f"_{direction.value}" if direction != Direction.NONE else ""
            style_str = f"_{style}" if style is not None else ""
            base_name = f"{element.value}{direction_str}{style_str}"
            name_increment = 0
            while base_name in used_names:
                base_name = (
                    f"{element.value}{direction_str}{style_str}_{name_increment}"
                )
                name_increment += 1
            used_names.append(base_name)
            image.save(
                os.path.join(
                    self._tile_data_dir,
                    f"{base_name}.png",
                ),
                "PNG",
                pnginfo=png_info,
            )
        self._tile_data = self._load_tile_data()
        if self._sample_data:
            self._classify_sample_data()
            self._queue.put((GUIEvent.SET_TRAINING_DATA, self._sample_data))
        print("Finished getting tile data")

    def _classify_sample_data(self):
        predicted_contents, debug_images = self.classify_tiles(
            {t["file_name"]: t["image"] for t in self._sample_data},
            {t["file_name"]: t["minimap_color"] for t in self._sample_data},
            return_debug_images=True,
        )
        for entry in self._sample_data:
            entry["predicted_content"] = predicted_contents[entry["file_name"]]
            entry["debug_images"] = debug_images[entry["file_name"]]

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
        is True, return a second dict of images.
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

    async def generate_sample_data(self):
        """Generate some sample data to test the classifier."""
        print("Generating sample data...")
        await self._interface.initialize()
        await self._interface.clear_room()
        room = Room()

        elements = [
            (Element.FLOOR, Direction.NONE, 0, 0),
            (Element.BEETHRO, Direction.N, 0, 1),
            (Element.BEETHRO, Direction.N, 0, 2),
            (Element.BEETHRO, Direction.NE, 1, 1),
            (Element.FLOOR, Direction.NONE, 2, 1),
            (Element.BEETHRO, Direction.NW, 3, 1),
            (Element.ROACH, Direction.N, 2, 0),
            (Element.ROACH, Direction.NE, 3, 3),
            (Element.ROACH, Direction.SW, 3, 4),
            (Element.GREEN_DOOR_OPEN, Direction.NONE, 5, 5),
            (Element.ROACH, Direction.SE, 5, 5),
            (Element.WALL, Direction.NONE, 12, 25),
            (Element.WALL, Direction.NONE, 13, 25),
            (Element.WALL, Direction.NONE, 13, 24),
            (Element.WALL, Direction.NONE, 11, 26),
            (Element.WALL, Direction.NONE, 12, 26),
            (Element.FLOOR, Direction.NONE, 11, 27),
            (Element.FLOOR, Direction.NONE, 12, 27),
            (Element.FLOOR, Direction.NONE, 13, 27),
            (Element.FLOOR, Direction.NONE, 13, 26),
            (Element.FLOOR, Direction.NONE, 14, 25),
            (Element.FLOOR, Direction.NONE, 14, 24),
            (Element.WALL, Direction.NONE, 15, 23),
            (Element.WALL, Direction.NONE, 16, 22),
            (Element.FLOOR, Direction.NONE, 16, 23),
            (Element.BLUE_DOOR, Direction.NONE, 6, 5),
            (Element.BLUE_DOOR, Direction.NONE, 7, 5),
            (Element.BLUE_DOOR, Direction.NONE, 8, 5),
            (Element.BLUE_DOOR, Direction.NONE, 6, 6),
            (Element.BLUE_DOOR, Direction.NONE, 7, 6),
            (Element.BLUE_DOOR, Direction.NONE, 8, 6),
            (Element.BLUE_DOOR, Direction.NONE, 6, 7),
            (Element.BLUE_DOOR, Direction.NONE, 7, 7),
            (Element.BLUE_DOOR, Direction.NONE, 8, 7),
            (Element.OBSTACLE, Direction.NONE, 28, 5),
            (Element.FORCE_ARROW, Direction.NW, 9, 9),
            (Element.FORCE_ARROW, Direction.W, 7, 16),
        ]
        for (element, direction, x, y) in elements:
            await self._interface.place_element(element, direction, (x, y))
            room.place_element_like_editor(element, direction, (x, y))
        await self._interface.place_element(
            Element.FLOOR, Direction.NONE, (7, 16), style="road"
        )

        await self._interface.place_element(
            Element.WALL, Direction.NONE, (5, 10), (10, 15)
        )
        room.place_element_like_editor(Element.WALL, Direction.NONE, (5, 10), (10, 15))
        for x in range(5, 11):
            for y in range(10, 16):
                elements.append((Element.WALL, Direction.NONE, x, y))

        await self._interface.start_test_room((37, 31), Direction.SE)
        tiles, colors = await self._interface.get_tiles_and_colors()
        await self._interface.stop_test_room()
        if os.path.exists(self._sample_data_dir):
            shutil.rmtree(self._sample_data_dir)
        os.makedirs(self._sample_data_dir)
        for (element, direction, x, y) in elements:
            tile_info = room.get_tile((x, y))
            minimap_color = colors[(x, y)]
            png_info = PngInfo()
            png_info.add_text("tile_json", tile_info.to_json())
            png_info.add_text("minimap_color", json.dumps(minimap_color))
            image = PIL.Image.fromarray(tiles[(x, y)])
            image.save(
                os.path.join(
                    self._sample_data_dir,
                    f"{x}_{y}.png",
                ),
                "PNG",
                pnginfo=png_info,
            )
        print("Finished generating sample data")


def _preprocess_image(image, return_debug_images=False):
    """Pre-process an image before comparing it to others.

    This should be done both to input images when classifying,
    and tile data images when importing.

    Parameters
    ----------
    image
        Image to process, with floats.
    return_debug_images
        If true, also return a list of (name, image) tuples with
        intermediate images.

    Returns
    -------
    The processed image.
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

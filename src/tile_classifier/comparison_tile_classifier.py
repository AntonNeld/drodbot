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
            file_names = os.listdir(self._tile_data_dir)
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
                        "image": image_array,
                        "mask": numpy.logical_not(
                            find_color(image_array, (255, 0, 255))
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

    async def load_training_data(self):
        """Load the sample data and send it to the GUI.

        Has 'training' in the name to match the API of NeuralTileClassifier.
        Will be renamed once this classifier can be the standard one.
        """
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

    async def train_model(self):
        """Get tile data using the editor.

        The name is to match the API of NeuralTileClassifier.
        Will be renamed once this classifier can be the standard one.
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

        # Swords are ignored when placing, but will be used when annotating
        elements = (
            _get_sworded_element_placement(Element.BEETHRO, Element.BEETHRO_SWORD, 0, 0)
            + _get_fully_directional_element_placement(Element.ROACH, 0, 3)
            + [
                (Element.FLOOR, Direction.NONE, 2, 2),
                (Element.FLOOR, Direction.NONE, 3, 2),
            ]
            + _get_nondirectional_edges_element_placement(Element.WALL, 1, 4)
            + _get_nondirectional_edges_element_placement(Element.YELLOW_DOOR, 1, 9)
            + _get_nondirectional_edges_element_placement(Element.BLUE_DOOR, 1, 14)
            + _get_nondirectional_edges_element_placement(Element.GREEN_DOOR, 1, 19)
            + _get_nondirectional_edges_element_placement(
                Element.YELLOW_DOOR_OPEN, 11, 9
            )
            + _get_nondirectional_edges_element_placement(
                Element.BLUE_DOOR_OPEN, 11, 14
            )
            + _get_nondirectional_edges_element_placement(
                Element.GREEN_DOOR_OPEN, 11, 19
            )
        )
        for (element, direction, x, y) in elements:
            if element not in [Element.BEETHRO_SWORD]:
                await self._interface.place_element(element, direction, (x, y))

        # Replace the normal central wall with a hard wall
        await self._interface.place_element(
            Element.WALL, Direction.NONE, (2, 6), style="hard"
        )

        await self._interface.start_test_room((37, 31), Direction.SE)
        tiles, _ = await self._interface.get_tiles_and_colors()
        await self._interface.stop_test_room()
        if os.path.exists(self._tile_data_dir):
            shutil.rmtree(self._tile_data_dir)
        os.makedirs(self._tile_data_dir)
        used_names = []
        for (element, direction, x, y) in elements:
            png_info = PngInfo()
            png_info.add_text("element", element.value)
            png_info.add_text("direction", direction.value)
            image = PIL.Image.fromarray(tiles[(x, y)])
            base_name = f"{element.value}_{direction.value}"
            name_increment = 0
            while base_name in used_names:
                base_name = f"{element.value}_{direction.value}_{name_increment}"
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

    async def save_model_weights(self):
        print("Saving model weights is not applicable with the current classifier")

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
        # TODO: Use numpy arrays for performance, once the logic is done
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
        for key, image in tiles.items():
            found_elements_mask = numpy.ones((TILE_SIZE, TILE_SIZE), dtype=bool)
            passes = 1
            while classified_tiles[key].room_piece == (
                Element.UNKNOWN,
                Direction.UNKNOWN,
            ):
                average_diffs = []
                alternatives = [
                    d
                    for d in self._tile_data
                    if (
                        d["layer"] == "swords"
                        and classified_tiles[key].monster
                        == (Element.UNKNOWN, Direction.UNKNOWN)
                    )
                    or (
                        d["layer"] != "swords"
                        and getattr(classified_tiles[key], d["layer"])
                        == (Element.UNKNOWN, Direction.UNKNOWN)
                    )
                    and numpy.sum(
                        numpy.logical_and(d["mask"], found_elements_mask) != 0
                    )
                ]
                for alternative in alternatives:
                    diff = numpy.sqrt(
                        numpy.sum(
                            (image.astype(float) - alternative["image"].astype(float))
                            ** 2,
                            axis=-1,
                        )
                    )
                    mask = numpy.logical_and(alternative["mask"], found_elements_mask)
                    masked_diff = diff * mask
                    debug_images[key].append(
                        (
                            f"Pass {passes}, masked diff "
                            f"with {alternative['file_name']}",
                            masked_diff,
                        )
                    )
                    average_diff = numpy.sum(masked_diff) / numpy.sum(mask)
                    average_diffs.append(average_diff)
                best_match_index, _ = min(
                    ((i, v) for (i, v) in enumerate(average_diffs)), key=lambda x: x[1]
                )
                element = alternatives[best_match_index]["element"]
                direction = alternatives[best_match_index]["direction"]
                debug_images[key].append(
                    (
                        f"=Pass {passes}, selected "
                        f"{alternatives[best_match_index]['file_name']}=",
                        alternatives[best_match_index]["image"],
                    )
                )
                element_mask = alternatives[best_match_index]["mask"]
                found_elements_mask = numpy.logical_and(
                    found_elements_mask, numpy.logical_not(element_mask)
                )
                passes += 1
                layer = alternatives[best_match_index]["layer"]
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

        if return_debug_images:
            return classified_tiles, debug_images
        return classified_tiles

    async def generate_training_data(self):
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
            (Element.WALL, Direction.NONE, 12, 26),
            (Element.FLOOR, Direction.NONE, 13, 26),
            (Element.BLUE_DOOR, Direction.NONE, 6, 5),
            (Element.BLUE_DOOR, Direction.NONE, 7, 5),
            (Element.BLUE_DOOR, Direction.NONE, 8, 5),
            (Element.BLUE_DOOR, Direction.NONE, 6, 6),
            (Element.BLUE_DOOR, Direction.NONE, 7, 6),
            (Element.BLUE_DOOR, Direction.NONE, 8, 6),
            (Element.BLUE_DOOR, Direction.NONE, 6, 7),
            (Element.BLUE_DOOR, Direction.NONE, 7, 7),
            (Element.FLOOR, Direction.NONE, 8, 7),
        ]
        for (element, direction, x, y) in elements:
            await self._interface.place_element(element, direction, (x, y))
            room.place_element_like_editor(element, direction, (x, y))

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


def _get_sworded_element_placement(element, sword, x, y):
    """Get a list of sworded elements and directions.

    This can be used to place sworded elements in the editor,
    in a compact way that includes all directions.

    Parameters
    ----------
    element
        The element to place.
    sword
        The sword belonging to the element.
    x
        X coordinate of the upper left corner of the pattern.
    y
        Y coordinate of the upper left corner of the pattern.
    """
    return [
        (element, Direction.N, x + 0, y + 1),
        (sword, Direction.N, x + 0, y + 0),
        (element, Direction.NE, x + 0, y + 2),
        (sword, Direction.NE, x + 1, y + 1),
        (element, Direction.E, x + 1, y + 0),
        (sword, Direction.E, x + 2, y + 0),
        (element, Direction.SE, x + 3, y + 0),
        (sword, Direction.SE, x + 4, y + 1),
        (element, Direction.S, x + 5, y + 1),
        (sword, Direction.S, x + 5, y + 2),
        (element, Direction.SW, x + 2, y + 1),
        (sword, Direction.SW, x + 1, y + 2),
        (element, Direction.W, x + 5, y + 0),
        (sword, Direction.W, x + 4, y + 0),
        (element, Direction.NW, x + 4, y + 2),
        (sword, Direction.NW, x + 3, y + 1),
    ]


def _get_fully_directional_element_placement(element, x, y):
    """Get a list of directional elements and directions.

    This can be used to place elements in the editor,
    in a compact way that includes all directions. This function is
    for fully directional elements, i.e. those that can face in 8 directions.

    Parameters
    ----------
    element
        The element to place.
    x
        X coordinate of the upper left corner of the pattern.
    y
        Y coordinate of the upper left corner of the pattern.
    """
    return [
        (element, Direction.N, x + 0, y + 0),
        (element, Direction.NE, x + 1, y + 0),
        (element, Direction.E, x + 2, y + 0),
        (element, Direction.SE, x + 3, y + 0),
        (element, Direction.S, x + 0, y + 1),
        (element, Direction.SW, x + 1, y + 1),
        (element, Direction.W, x + 2, y + 1),
        (element, Direction.NW, x + 3, y + 1),
    ]


def _get_nondirectional_edges_element_placement(element, x, y):
    """Get a list of nondirectional elements (and NONE directions).

    This can be used to place elements in the editor,
    to get several types of edges

    Parameters
    ----------
    element
        The element to place.
    x
        X coordinate of the upper left corner of the pattern.
    y
        Y coordinate of the upper left corner of the pattern.
    """
    return [
        # Little compact square
        (element, Direction.NONE, x + 0, y + 1),
        (element, Direction.NONE, x + 1, y + 1),
        (element, Direction.NONE, x + 2, y + 1),
        (element, Direction.NONE, x + 0, y + 2),
        (element, Direction.NONE, x + 1, y + 2),
        (element, Direction.NONE, x + 2, y + 2),
        (element, Direction.NONE, x + 0, y + 3),
        (element, Direction.NONE, x + 1, y + 3),
        (element, Direction.NONE, x + 2, y + 3),
        # Big holey square
        (element, Direction.NONE, x + 4, y + 0),
        (element, Direction.NONE, x + 4, y + 1),
        (element, Direction.NONE, x + 4, y + 2),
        (element, Direction.NONE, x + 4, y + 3),
        (element, Direction.NONE, x + 4, y + 4),
        (element, Direction.NONE, x + 5, y + 0),
        (element, Direction.NONE, x + 5, y + 2),
        (element, Direction.NONE, x + 5, y + 4),
        (element, Direction.NONE, x + 6, y + 0),
        (element, Direction.NONE, x + 6, y + 1),
        (element, Direction.NONE, x + 6, y + 2),
        (element, Direction.NONE, x + 6, y + 3),
        (element, Direction.NONE, x + 6, y + 4),
        (element, Direction.NONE, x + 7, y + 0),
        (element, Direction.NONE, x + 7, y + 2),
        (element, Direction.NONE, x + 7, y + 4),
        (element, Direction.NONE, x + 8, y + 0),
        (element, Direction.NONE, x + 8, y + 1),
        (element, Direction.NONE, x + 8, y + 2),
        (element, Direction.NONE, x + 8, y + 3),
        (element, Direction.NONE, x + 8, y + 4),
    ]

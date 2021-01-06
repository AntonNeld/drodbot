import json
import os
import os.path
import shutil

import numpy
import PIL
from PIL.PngImagePlugin import PngInfo

from common import (
    ImageProcessingStep,
    TILE_PROCESSING_STEPS,
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
                tile_data.append(
                    {
                        "image": image_array,
                        "mask": numpy.expand_dims(
                            numpy.logical_not(find_color(image_array, (255, 255, 255))),
                            2,
                        )
                        * numpy.ones(3),
                        "element": next(
                            e for e in Element if e.value == image.info["element"]
                        ),
                        "direction": next(
                            d for d in Direction if d.value == image.info["direction"]
                        ),
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
        elements = [
            (Element.BEETHRO, Direction.N, 0, 1),
            (Element.BEETHRO_SWORD, Direction.N, 0, 0),
            (Element.BEETHRO, Direction.NE, 0, 2),
            (Element.BEETHRO_SWORD, Direction.NE, 1, 1),
            (Element.BEETHRO, Direction.E, 1, 0),
            (Element.BEETHRO_SWORD, Direction.E, 2, 0),
            (Element.BEETHRO, Direction.SE, 3, 0),
            (Element.BEETHRO_SWORD, Direction.SE, 4, 1),
            (Element.BEETHRO, Direction.S, 5, 1),
            (Element.BEETHRO_SWORD, Direction.S, 5, 2),
            (Element.BEETHRO, Direction.SW, 2, 1),
            (Element.BEETHRO_SWORD, Direction.SW, 1, 2),
            (Element.BEETHRO, Direction.W, 5, 0),
            (Element.BEETHRO_SWORD, Direction.W, 4, 0),
            (Element.BEETHRO, Direction.NW, 4, 2),
            (Element.BEETHRO_SWORD, Direction.NW, 3, 1),
            (Element.FLOOR, Direction.NONE, 2, 2),
            (Element.FLOOR, Direction.NONE, 3, 2),
        ]
        for (element, direction, x, y) in elements:
            if element not in [Element.BEETHRO_SWORD]:
                await self._interface.place_element(element, direction, (x, y))

        await self._interface.start_test_room((37, 31), Direction.SE)
        tiles, _ = await self._interface.get_tiles_and_colors()
        await self._interface.stop_test_room()
        if os.path.exists(self._tile_data_dir):
            shutil.rmtree(self._tile_data_dir)
        os.makedirs(self._tile_data_dir)
        for (element, direction, x, y) in elements:
            png_info = PngInfo()
            png_info.add_text("element", element.value)
            png_info.add_text("direction", direction.value)
            image = PIL.Image.fromarray(tiles[(x, y)])
            image.save(
                os.path.join(
                    self._tile_data_dir,
                    f"{element.value}_{direction.value}.png",
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
            entry["debug_images"] = {
                step: debug_images[step][entry["file_name"]]
                for step in TILE_PROCESSING_STEPS
            }

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
            If True, return a second dict where the keys are ImageProcessingSteps,
            and the values are dicts like `tiles` but with intermediate images.

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
        debug_images = {step: {} for step in TILE_PROCESSING_STEPS}
        for key, image in tiles.items():
            average_diffs = []
            for alternative in self._tile_data:
                squared_diff = (image - alternative["image"]) ** 2
                masked_diff = squared_diff * alternative["mask"]
                average_diff = numpy.sum(masked_diff) / numpy.sum(alternative["mask"])
                average_diffs.append(average_diff)
            best_match_index, _ = min(
                ((i, v) for (i, v) in enumerate(average_diffs)), key=lambda x: x[1]
            )
            debug_images[ImageProcessingStep.DIFF_TILES][key] = (
                image - self._tile_data[best_match_index]["image"]
            ) ** 2
            debug_images[ImageProcessingStep.MASK_DIFFS][key] = (
                debug_images[ImageProcessingStep.DIFF_TILES][key]
                * self._tile_data[best_match_index]["mask"]
            )
            element = self._tile_data[best_match_index]["element"]
            direction = self._tile_data[best_match_index]["direction"]
            layers = [
                # If it's a sword, we just ignore it
                ("monster", MONSTERS),
                ("item", ITEMS),
                ("checkpoint", CHECKPOINTS),
                ("floor_control", FLOOR_CONTROLS),
                ("room_piece", ROOM_PIECES),
            ]
            for index, (layer, layer_elements) in enumerate(layers):
                if element in layer_elements:
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
                    for layer_above, _ in layers[:index]:
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

        # Swords are ignored when placing, but will be used when annotating
        elements = [
            (Element.FLOOR, Direction.NONE, 0, 0),
            (Element.BEETHRO, Direction.N, 0, 1),
            (Element.BEETHRO, Direction.N, 0, 2),
            (Element.BEETHRO, Direction.NE, 1, 1),
            (Element.FLOOR, Direction.NONE, 2, 1),
            (Element.BEETHRO, Direction.NW, 3, 1),
            (Element.FLOOR, Direction.NONE, 2, 0),
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

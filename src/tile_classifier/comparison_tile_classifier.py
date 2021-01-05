import json
import os
import os.path

import numpy
import PIL
from PIL.PngImagePlugin import PngInfo

from common import (
    GUIEvent,
    Element,
    Direction,
    Tile,
)


class ComparisonTileClassifier:
    def __init__(self, tile_data_dir, sample_data_dir, editor_interface, window_queue):
        self._tile_data_dir = tile_data_dir
        self._sample_data_dir = sample_data_dir
        self._interface = editor_interface
        self._sample_data = []
        self._queue = window_queue

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
        ]
        for (element, direction, x, y) in elements:
            if element not in [Element.BEETHRO_SWORD]:
                await self._interface.place_element(element, direction, (x, y))
        print("Finished getting tile data")

    async def save_model_weights(self):
        print("Saving model weights is not applicable with the current classifier")

    def _classify_sample_data(self):
        predicted_contents = self.classify_tiles(
            {t["file_name"]: t["image"] for t in self._sample_data},
            {t["file_name"]: t["minimap_color"] for t in self._sample_data},
        )
        for entry in self._sample_data:
            entry["predicted_content"] = predicted_contents[entry["file_name"]]

    def classify_tiles(self, tiles, minimap_colors):
        """Classify the given tiles.

        Parameters
        ----------
        tiles
            A dict with tile images as the values.
        minimap_colors
            A dict with the same keys as `tiles` and (r, g, b) color tuples
            as the values.

        Returns
        -------
        A dict with the same keys as `tiles`, but Tile objects
        representing the tile contents as the values.
        """

        return {
            key: Tile(room_piece=(Element.UNKNOWN, Direction.UNKNOWN)) for key in tiles
        }

    async def generate_training_data(self):
        print("For now, generate sample data with the other classifier")


def _save_tile_png(coords, tile, tile_info, minimap_color, base_name, directory):
    png_info = PngInfo()
    png_info.add_text("tile_json", tile_info.to_json())
    png_info.add_text("minimap_color", json.dumps(minimap_color))
    # Save the image with a random name
    image = PIL.Image.fromarray(tile)
    image.save(
        os.path.join(
            directory,
            f"{base_name}_{coords[0]}_{coords[1]}.png",
        ),
        "PNG",
        pnginfo=png_info,
    )

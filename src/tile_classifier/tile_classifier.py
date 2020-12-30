import os
import os.path
import random
import string

import numpy
import PIL
from PIL.PngImagePlugin import PngInfo

from tensorflow import keras

from common import ImageProcessingStep, GUIEvent, Element, Direction, Room, Tile


class TileClassifier:
    def __init__(self, training_data_dir, weights_dir, drod_interface, window_queue):
        self._training_data_dir = training_data_dir
        self._weights_path = os.path.join(weights_dir, "tile_classifier_weights")
        self._interface = drod_interface
        self._data = []
        self._queue = window_queue
        self._model = _new_model()
        try:
            self._model.load_weights(self._weights_path)
        except ValueError:
            print("No model weights found, not loading any")

    async def load_training_data(self):
        """Load the training data and send it to the GUI."""
        self._data = []
        try:
            file_names = os.listdir(self._training_data_dir)
        except FileNotFoundError:
            print("No training data directory found")
            self._queue.put((GUIEvent.TRAINING_DATA, self._data))
            return
        for file_name in file_names:
            image = PIL.Image.open(os.path.join(self._training_data_dir, file_name))
            content = Tile.from_json(image.info["tile_json"])
            self._data.append(
                {
                    "image": numpy.array(image),
                    "real_content": content,
                    "file_name": file_name,
                }
            )
        self._classify_training_data()
        self._queue.put((GUIEvent.TRAINING_DATA, self._data))

    async def train_model(self):
        """Train a model from the current training data."""
        self._model = _new_model()
        images_array = numpy.stack([t["image"] for t in self._data], axis=0)
        # For now, just check whether the tile has a wall
        is_wall = numpy.array(
            [t["real_content"].room_piece[0] == Element.WALL for t in self._data],
            dtype=numpy.uint8,
        )
        # Let 10% of our data be for validation
        validation_start = images_array.shape[0] // 10
        self._model.fit(
            images_array[:validation_start],
            is_wall[:validation_start],
            epochs=10,
            validation_data=(
                images_array[validation_start:],
                is_wall[validation_start:],
            ),
        )
        self._classify_training_data()
        self._queue.put((GUIEvent.TRAINING_DATA, self._data))
        print("Training complete")

    async def save_model_weights(self):
        self._model.save_weights(self._weights_path)
        print("Saved model weights")

    def _classify_training_data(self):
        predicted_contents = self.classify_tiles(
            {t["file_name"]: t["image"] for t in self._data}
        )
        for entry in self._data:
            entry["predicted_content"] = predicted_contents[entry["file_name"]]

    def classify_tiles(self, tiles):
        """Classify the given tiles according to the current model.

        Parameters
        ----------
        tiles
            A dict with tile images as the values.

        Returns
        -------
        A dict with the same keys as `tiles`, but Tile objects
        representing the tile contents as the values.
        """
        keys, images = zip(*tiles.items())
        images_array = numpy.stack(images, axis=0)
        results = self._model.predict(images_array)
        best_guesses = numpy.argmax(results, axis=-1)
        classified_tiles = {}
        for index, key in enumerate(keys):
            classified_tiles[key] = Tile(
                room_piece=(
                    Element.WALL if best_guesses[index] == 1 else Element.FLOOR,
                    Direction.NONE,
                )
            )
        return classified_tiles

    async def generate_training_data(self):
        """Generate data for training the classification model.

        With the editor open, this method will add elements to the room
        with various floors, and save the tiles as images.
        The images are annotated with the tile contents as metadata.
        """
        print("Generating training data")
        await self._interface.initialize(editor=True)
        await self._interface.editor_clear_room()
        room = await self._generate_room()

        # Starting position when testing
        room.place_element_like_editor(Element.BEETHRO, Direction.SE, (37, 31))

        await self._interface.editor_start_test_room((37, 31), Direction.SE)
        visual_info = await self._interface.get_view(
            step=ImageProcessingStep.EXTRACT_TILES
        )
        await self._interface.editor_stop_test_room()

        if not os.path.exists(self._training_data_dir):
            os.makedirs(self._training_data_dir)
        random_string = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        for coords, tile in visual_info["tiles"].items():
            # Annotate the image with the tile contents
            tile_info = room.get_tile(coords)
            _save_tile_png(
                coords, tile, tile_info, random_string, self._training_data_dir
            )
        # Place a conquer token under the starting position and go again,
        # to capture triggered conquer tokens in the screenshot
        await self._interface.editor_place_element(
            Element.CONQUER_TOKEN, Direction.NONE, (37, 31)
        )
        room.place_element_like_editor(Element.CONQUER_TOKEN, Direction.NONE, (37, 31))
        await self._interface.editor_start_test_room((37, 31), Direction.SE)
        visual_info = await self._interface.get_view(
            step=ImageProcessingStep.EXTRACT_TILES
        )
        await self._interface.editor_stop_test_room()
        for coords in room.find_coordinates(Element.CONQUER_TOKEN):
            tile = visual_info["tiles"][coords]
            tile_info = room.get_tile(coords)
            tile_info.item = (Element.TRIGGERED_CONQUER_TOKEN, Direction.NONE)
            _save_tile_png(
                coords, tile, tile_info, f"{random_string}v", self._training_data_dir
            )
        print("Finished generating training data")

    async def _generate_room(self):
        room = Room()
        for start, end in [
            ((6, 3), (13, 8)),
            ((4, 5), (5, 5)),
            ((10, 9), (10, 11)),
            ((12, 9), (12, 11)),
            ((14, 6), (23, 6)),
            ((23, 7), (23, 9)),
            ((9, 15), (11, 15)),
            ((17, 15), (17, 16)),
            ((18, 16), None),
            ((22, 13), (24, 15)),
            ((10, 26), None),
            ((10, 27), (11, 28)),
            ((10, 29), (12, 30)),
            ((7, 31), (12, 31)),
        ]:
            await self._interface.editor_place_element(
                Element.WALL, Direction.NONE, start, end
            )
            room.place_element_like_editor(Element.WALL, Direction.NONE, start, end)
        for coords in [
            (9, 5),
            (6, 8),
            (23, 9),
            (29, 8),
            (30, 8),
            (6, 15),
            (10, 16),
            (21, 17),
            (12, 28),
        ]:
            await self._interface.editor_place_element(
                Element.CONQUER_TOKEN, Direction.NONE, coords
            )
            room.place_element_like_editor(
                Element.CONQUER_TOKEN, Direction.NONE, coords
            )
        for coords, direction in [
            ((3, 3), Direction.N),
            ((5, 6), Direction.NE),
            ((11, 9), Direction.SE),
            ((28, 4), Direction.W),
            ((17, 10), Direction.SW),
            ((10, 14), Direction.E),
            ((6, 17), Direction.NW),
            ((19, 19), Direction.S),
            ((13, 29), Direction.NW),
        ]:
            await self._interface.editor_place_element(
                Element.BEETHRO, direction, coords
            )
            room.place_element_like_editor(Element.BEETHRO, direction, coords)
        return room


def _save_tile_png(coords, tile, tile_info, base_name, directory):
    png_info = PngInfo()
    png_info.add_text("tile_json", tile_info.to_json())
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


def _new_model():
    model = keras.models.Sequential(
        [
            keras.layers.experimental.preprocessing.Rescaling(scale=1.0 / 255),
            keras.layers.Flatten(input_shape=[22, 22, 3]),
            keras.layers.Dense(300, activation="relu"),
            keras.layers.Dense(100, activation="relu"),
            keras.layers.Dense(100, activation="relu"),
            keras.layers.Dense(100, activation="relu"),
            keras.layers.Dense(2, activation="softmax"),
        ]
    )
    model.compile(
        loss="sparse_categorical_crossentropy",
        optimizer="sgd",
        metrics=["accuracy"],
    )
    return model

import asyncio
import copy
import json
import os
import os.path
import random
import string

import numpy
import PIL
from PIL.PngImagePlugin import PngInfo

from tensorflow import keras

from common import (
    GUIEvent,
    Element,
    Direction,
    Room,
    Tile,
    ROOM_WIDTH_IN_TILES,
    ROOM_HEIGHT_IN_TILES,
    ROOM_PIECES,
    ITEMS,
    MONSTERS,
    ALLOWED_DIRECTIONS,
)

LAYERS = [
    ("room_piece", [(e, d) for e in ROOM_PIECES for d in ALLOWED_DIRECTIONS[e]]),
    ("item", [(e, d) for e in ITEMS for d in ALLOWED_DIRECTIONS[e]]),
    ("monster", [(e, d) for e in MONSTERS for d in ALLOWED_DIRECTIONS[e]]),
]


class TileClassifier:
    def __init__(self, training_data_dir, weights_dir, editor_interface, window_queue):
        self._training_data_dir = training_data_dir
        self._weights_dir = weights_dir
        self._interface = editor_interface
        self._data = []
        self._queue = window_queue
        self._models = {}
        for layer, elements in LAYERS:
            self._models[layer] = _new_model(len(elements))
            try:
                self._models[layer].load_weights(os.path.join(self._weights_dir, layer))
            except ValueError:
                print(f"No model weights found for {layer}, not loading any")

    async def load_training_data(self):
        """Load the training data and send it to the GUI."""
        print("Loading training data...")
        self._data = []
        try:
            file_names = os.listdir(self._training_data_dir)
        except FileNotFoundError:
            print("No training data directory found")
            self._queue.put((GUIEvent.SET_TRAINING_DATA, self._data))
            return
        for file_name in file_names:
            image = PIL.Image.open(os.path.join(self._training_data_dir, file_name))
            content = Tile.from_json(image.info["tile_json"])
            minimap_color = tuple(json.loads(image.info["minimap_color"]))
            self._data.append(
                {
                    "image": numpy.array(image),
                    "real_content": content,
                    "file_name": file_name,
                    "minimap_color": minimap_color,
                }
            )
        self._classify_training_data()
        self._queue.put((GUIEvent.SET_TRAINING_DATA, self._data))
        print("Loaded training data")

    async def train_model(self):
        """Train a model from the current training data.

        Set the resulting model as the current model.
        """
        for layer, elements in LAYERS:
            print(f"Training model for {layer}")
            # Remove excess data so there are equal amounts of each element
            curated_data = copy.copy(self._data)
            random.shuffle(curated_data)
            counts = {}
            for t in curated_data:
                element = getattr(t["real_content"], layer)[0]
                if element not in counts:
                    counts[element] = 0
                counts[element] += 1
            target_amount = min(counts.values())
            print(f"Curating dataset to have {target_amount} of each type.")
            for element, amount in counts.items():
                for _ in range(amount - target_amount):
                    index = next(
                        i
                        for i, t in enumerate(curated_data)
                        if getattr(t["real_content"], layer)[0] == element
                    )
                    curated_data.pop(index)

            images_array = numpy.stack([t["image"] for t in curated_data], axis=0)
            self._models[layer] = _new_model(len(elements))
            element = numpy.array(
                [
                    elements.index(getattr(t["real_content"], layer))
                    for t in curated_data
                ],
                dtype=numpy.uint8,
            )
            # Let 10% of our data be for validation
            validation_start = images_array.shape[0] // 10
            self._models[layer].fit(
                images_array[:validation_start],
                element[:validation_start],
                epochs=5,
                validation_data=(
                    images_array[validation_start:],
                    element[validation_start:],
                ),
            )
        self._classify_training_data()
        self._queue.put((GUIEvent.SET_TRAINING_DATA, self._data))
        print("Training complete")

    async def save_model_weights(self):
        for layer, _ in LAYERS:
            self._models[layer].save_weights(os.path.join(self._weights_dir, layer))
        print("Saved model weights")

    def _classify_training_data(self):
        predicted_contents = self.classify_tiles(
            {t["file_name"]: t["image"] for t in self._data},
            {t["file_name"]: t["minimap_color"] for t in self._data},
        )
        for entry in self._data:
            entry["predicted_content"] = predicted_contents[entry["file_name"]]

    def classify_tiles(self, tiles, minimap_colors):
        """Classify the given tiles according to the current model.

        Parameters
        ----------
        tiles
            A dict with tile images as the values.
        minimap_colors
            A dict with the same keys as `tiles` and (r, g, b) color tuples
            as the values. If given, use this to help classify the trickier
            elements. Otherwise, only rely on the neural network.

        Returns
        -------
        A dict with the same keys as `tiles`, but Tile objects
        representing the tile contents as the values.
        """
        keys, images = zip(*tiles.items())
        images_array = numpy.stack(images, axis=0)
        classified_tiles = {
            key: Tile(room_piece=(Element.UNKNOWN, Direction.UNKNOWN)) for key in keys
        }
        for layer, elements in LAYERS:
            results = self._models[layer].predict(images_array)
            for index, key in enumerate(keys):
                probabilities = _exclude_wrong_colors(
                    results[index, :], minimap_colors[key], layer, elements
                )
                setattr(
                    classified_tiles[key],
                    layer,
                    elements[numpy.argmax(probabilities)],
                )
        return classified_tiles

    async def generate_training_data(self):
        """Generate data for training the classification model.

        With the editor open, this method will add elements to the room
        and save the tiles as images. The images are annotated with the
        tile contents as metadata.
        """
        print("Generating training data...")
        await self._interface.initialize()
        await self._interface.clear_room()
        room = await self._generate_room()

        # Starting position when testing
        room.place_element_like_editor(Element.BEETHRO, Direction.SE, (37, 31))

        await self._interface.select_first_style()
        # Wait a bit, since loading the room may take some time if the computer is busy
        await asyncio.sleep(10)

        for _ in range(13):  # There are 13 room styles
            await self._interface.start_test_room((37, 31), Direction.SE)
            tiles, colors = await self._interface.get_tiles_and_colors()
            await self._interface.stop_test_room()

            if not os.path.exists(self._training_data_dir):
                os.makedirs(self._training_data_dir)
            random_string = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=5)
            )
            for coords, tile in tiles.items():
                # Annotate the image with the tile contents
                tile_info = room.get_tile(coords)
                minimap_color = colors[coords]
                _save_tile_png(
                    coords,
                    tile,
                    tile_info,
                    minimap_color,
                    random_string,
                    self._training_data_dir,
                )
            # Place a conquer token under the starting position and go again,
            # to capture triggered conquer tokens in the screenshot
            await self._interface.place_element(
                Element.CONQUER_TOKEN, Direction.NONE, (37, 31)
            )
            room.place_element_like_editor(
                Element.CONQUER_TOKEN, Direction.NONE, (37, 31)
            )
            await self._interface.start_test_room((37, 31), Direction.SE)
            tiles, colors = await self._interface.get_tiles_and_colors()
            await self._interface.stop_test_room()
            for coords in room.find_coordinates(Element.CONQUER_TOKEN):
                tile = tiles[coords]
                tile_info = room.get_tile(coords)
                minimap_color = colors[coords]
                _save_tile_png(
                    coords,
                    tile,
                    tile_info,
                    minimap_color,
                    f"{random_string}v",
                    self._training_data_dir,
                )
            # Remove the conquer token for the next iteration
            await self._interface.clear_tile((37, 31))
            room.set_tile((37, 31), Tile(room_piece=(Element.FLOOR, Direction.NONE)))
            await self._interface.select_next_style()
        print("Finished generating training data")

    async def _generate_room(self):
        room = Room()
        # Mask out the reserved tile in the bottom right, so we can place
        # Beethro and a conquer token there
        mask = numpy.ones((ROOM_WIDTH_IN_TILES, ROOM_HEIGHT_IN_TILES), dtype=bool)
        mask[-1, -1] = False
        # Place the monster layer first, so we can use copy_characters
        # in EditorInterface.place_element
        await self._randomly_place_element(
            room,
            Element.BEETHRO,
            [
                Direction.SE,
                Direction.S,
                Direction.SW,
                Direction.W,
                Direction.NW,
                Direction.N,
                Direction.NE,
                Direction.E,
            ],
            0.5,
            mask=mask,
        )
        await self._randomly_place_element(
            room, Element.WALL, Direction.NONE, 0.5, mask=mask
        )
        # Since we will duplicate the tiles with conquer tokens, decrease the
        # probability so the number of tiles with and without will match
        await self._randomly_place_element(
            room, Element.CONQUER_TOKEN, Direction.NONE, 0.33, mask=mask
        )

        return room

    async def _randomly_place_element(
        self, room, element, direction, probability, mask=None
    ):
        """Place the given element randomly in the editor and given room.

        Parameters
        ----------
        room
            A Room instance to keep track of the room contents. If it matches the
            room state before this method is called, it will also match it after.
        element
            The element to place.
        direction
            The direction of the element to place. If it is an iterable, choose
            randomly from the given directions for each tile.
        probability
            The probability of a given tile containing the element.
        mask
            An optional boolean array that is True where elements can be
            placed and False elsewhere.

        Returns
        -------
        The locations where the element was placed, as a boolean numpy array.
        """
        has_element = (
            numpy.random.default_rng().random(
                (ROOM_WIDTH_IN_TILES, ROOM_HEIGHT_IN_TILES)
            )
            < probability
        )
        if mask is not None:
            has_element = has_element * mask

        try:
            len(direction)
            directions = direction
        except TypeError:  # direction is not an iterable
            directions = [direction]

        direction_map = numpy.random.default_rng().integers(
            0, len(directions), size=has_element.shape
        )

        for direction_index in range(len(directions)):
            for position in numpy.argwhere(
                numpy.logical_and(direction_map == direction_index, has_element)
            ):
                element_direction = directions[direction_index]
                await self._interface.place_element(
                    element, element_direction, position, copy_characters=True
                )
                room.place_element_like_editor(element, element_direction, position)

        return has_element


def _exclude_wrong_colors(probabilities, minimap_color, layer, elements):
    """Change probabilities of a predicted element to match minimap color.

    Set the probability of any element not matching the minimap color to 0,
    and normalize the rest.

    Parameters
    ----------
    probabilities
        A numpy array of probabilities, in the same order as `elements`.
    minimap_color
        The minimap color of the tile as an (r, g, b) tuple.
    layer
        The layer of the element.
    elements
        A list of elements, defining what the indices in `probabilities`
        map to.
    """
    # Since many minimap colors are unambiguous, init a probability vector with
    # only zeros, so we can just set an element to 1 and return.
    zero_probabilities = numpy.zeros(probabilities.shape)
    if layer == "room_piece":
        if minimap_color == (0, 0, 0):
            zero_probabilities[elements.index((Element.WALL, Direction.NONE))] = 1
            return zero_probabilities

    return probabilities


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


def _new_model(outputs):
    model = keras.models.Sequential(
        [
            keras.layers.experimental.preprocessing.Rescaling(scale=1.0 / 255),
            keras.layers.Flatten(input_shape=[22, 22, 3]),
            keras.layers.Dense(300, activation="relu"),
            keras.layers.Dense(100, activation="relu"),
            keras.layers.Dense(100, activation="relu"),
            keras.layers.Dense(100, activation="relu"),
            keras.layers.Dense(outputs, activation="softmax"),
        ]
    )
    model.compile(
        loss="sparse_categorical_crossentropy",
        optimizer="sgd",
        metrics=["accuracy"],
    )
    return model

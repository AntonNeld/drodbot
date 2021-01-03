import asyncio
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
    ITEMS,
    MONSTERS,
    ALLOWED_DIRECTIONS,
)


class TileClassifier:
    def __init__(self, training_data_dir, weights_dir, editor_interface, window_queue):
        self._training_data_dir = training_data_dir
        self._weights_dir = weights_dir
        self._interface = editor_interface
        self._data = []
        self._queue = window_queue
        self._models = {
            "ambiguous_items": {
                "layer": "item",
                "elements": [
                    (e, d)
                    for e in [e for e in ITEMS if e != Element.OBSTACLE]
                    for d in ALLOWED_DIRECTIONS[e]
                ],
            },
            "monster": {
                "layer": "monster",
                "elements": [(e, d) for e in MONSTERS for d in ALLOWED_DIRECTIONS[e]],
            },
        }
        for name, model in self._models.items():
            model["model"] = _new_model(len(model["elements"]))
            try:
                model["model"].load_weights(os.path.join(self._weights_dir, name))
            except ValueError:
                print(f"No model weights found for {name}, not loading any")

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
        """Train models from the current training data.

        Set the resulting models as the current models.
        """
        for name, model in self._models.items():
            print(f"Training model: {name}")
            # Remove tiles that are not in the model's scope, i.e. the element in the
            # model's layer is not a possible output of the model.
            curated_data = [
                t
                for t in self._data
                if getattr(t["real_content"], model["layer"]) in model["elements"]
            ]
            # Ensure there is an equal amount of each element in the training data.
            random.shuffle(curated_data)
            counts = {}
            for t in curated_data:
                element = getattr(t["real_content"], model["layer"])[0]
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
                        if getattr(t["real_content"], model["layer"])[0] == element
                    )
                    curated_data.pop(index)

            images_array = numpy.stack([t["image"] for t in curated_data], axis=0)
            model["model"] = _new_model(len(model["elements"]))
            element = numpy.array(
                [
                    model["elements"].index(getattr(t["real_content"], model["layer"]))
                    for t in curated_data
                ],
                dtype=numpy.uint8,
            )
            # Let 10% of our data be for validation
            validation_start = images_array.shape[0] // 10
            model["model"].fit(
                images_array[:validation_start],
                element[:validation_start],
                epochs=5,
                validation_data=(
                    images_array[validation_start:],
                    element[validation_start:],
                ),
            )
        print("Classifying training data...")
        self._classify_training_data()
        self._queue.put((GUIEvent.SET_TRAINING_DATA, self._data))
        print("Training complete")

    async def save_model_weights(self):
        for name, model in self._models.items():
            model["model"].save_weights(os.path.join(self._weights_dir, name))
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
        ambiguous_item_tiles = {}

        room_pieces = {}
        items = {}
        for key in tiles:
            color = minimap_colors[key]
            if color == (0, 0, 0):
                # TODO: This can be broken or secret walls too
                room_pieces[key] = (Element.WALL, Direction.NONE)
            elif color == (0, 0, 128):
                room_pieces[key] = (Element.PIT, Direction.NONE)
            elif color == (255, 128, 0):
                # TODO: This can be hold complete walls or hot tiles too
                room_pieces[key] = (Element.MASTER_WALL, Direction.NONE)
            elif color == (255, 255, 0):
                room_pieces[key] = (Element.YELLOW_DOOR, Direction.NONE)
            elif color == (255, 255, 164):
                room_pieces[key] = (Element.YELLOW_DOOR_OPEN, Direction.NONE)
            elif color == (0, 255, 0):
                room_pieces[key] = (Element.GREEN_DOOR, Direction.NONE)
            elif color == (128, 255, 128):  # Cleared room
                # TODO: This can be oremites too. They are not the same color, but
                # they disappear from the minimap when the room is just cleared.
                # TODO: This can be open green doors too
                room_pieces[key] = (Element.FLOOR, Direction.NONE)
            elif color == (0, 255, 255):
                room_pieces[key] = (Element.BLUE_DOOR, Direction.NONE)
            elif color == (164, 255, 255):
                room_pieces[key] = (Element.BLUE_DOOR_OPEN, Direction.NONE)
            elif color == (210, 210, 100):
                room_pieces[key] = (Element.STAIRS, Direction.NONE)
            elif color == (255, 200, 200):
                # This only appears in the editor, but we may as well have it
                room_pieces[key] = (Element.FLOOR, Direction.NONE)
            elif color == (255, 0, 0):  # Not cleared, required room
                # TODO: This can be red doors too
                room_pieces[key] = (Element.FLOOR, Direction.NONE)
            elif color == (255, 0, 255):  # Not cleared, not required room
                room_pieces[key] = (Element.FLOOR, Direction.NONE)
            elif color == (229, 229, 229):  # Cleared room, revisited
                room_pieces[key] = (Element.FLOOR, Direction.NONE)
            elif color == (128, 128, 128):
                # There is an obstacle on this tile, so we don't know what the
                # room piece is. It usually doesn't matter, so let's say it's floor.
                # TODO: Handle tunnels under obstacles, where it does matter.
                # TODO: Can be tunnels too
                room_pieces[key] = (Element.FLOOR, Direction.NONE)
            else:
                print(f"Unknown color {color}")
                room_pieces[key] = (Element.UNKNOWN, Direction.UNKNOWN)

            if color == (128, 128, 128):
                items[key] = (Element.OBSTACLE, Direction.NONE)
            else:
                ambiguous_item_tiles[key] = tiles[key]

        items = {
            **items,
            **_predict(ambiguous_item_tiles, self._models["ambiguous_items"]),
        }
        monsters = _predict(tiles, self._models["monster"])
        return {
            key: Tile(
                room_piece=room_pieces[key], item=items[key], monster=monsters[key]
            )
            for key in tiles
        }

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
        # Place some different floors. Have a mask rather than replacing the floors,
        # to speed things up a bit.
        floor_mask = await self._randomly_place_element(
            room, Element.FLOOR, Direction.NONE, 0.3, mask=mask, style="mosaic"
        )
        floor_mask = numpy.logical_and(floor_mask, mask)
        new_mask = await self._randomly_place_element(
            room, Element.FLOOR, Direction.NONE, 0.3, mask=floor_mask, style="road"
        )
        floor_mask = numpy.logical_and(floor_mask, new_mask)
        new_mask = await self._randomly_place_element(
            room, Element.FLOOR, Direction.NONE, 0.3, mask=floor_mask, style="grass"
        )
        floor_mask = numpy.logical_and(floor_mask, new_mask)
        new_mask = await self._randomly_place_element(
            room, Element.FLOOR, Direction.NONE, 0.3, mask=floor_mask, style="dirt"
        )
        floor_mask = numpy.logical_and(floor_mask, new_mask)
        new_mask = await self._randomly_place_element(
            room, Element.FLOOR, Direction.NONE, 0.3, mask=floor_mask, style="alternate"
        )

        await self._randomly_place_element(
            room, Element.WALL, Direction.NONE, 0.2, mask=mask
        )
        # Since we will duplicate the tiles with conquer tokens, decrease the
        # probability so the number of tiles with and without will match
        await self._randomly_place_element(
            room, Element.CONQUER_TOKEN, Direction.NONE, 0.33, mask=mask
        )

        return room

    async def _randomly_place_element(
        self, room, element, direction, probability, mask=None, style=None
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
        style
            The style to pass on to EditorInterface.place_element().

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
                    element,
                    element_direction,
                    position,
                    copy_characters=True,
                    style=style,
                )
                room.place_element_like_editor(element, element_direction, position)

        return has_element


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


def _predict(tiles, model):
    """Predict the element and direction in the given tiles.

    The layer depends on the model.

    Parameters
    ----------
    tiles
        Dict with tile images as the values.
    model
        Dict with the keys "model" (the actual model) and "elements"
        (list of element-direction pairs, mapping the indices in the
        model output).

    Returns
    -------
    Dict with the same keys as `tiles`, but the values are element-direction
    pairs from `model["elements"]`.
    """
    keys, images = zip(*tiles.items())
    images_array = numpy.stack(images, axis=0)
    classified_tiles = {}
    results = model["model"].predict(images_array)
    for index, key in enumerate(keys):
        probabilities = results[index, :]
        classified_tiles[key] = model["elements"][numpy.argmax(probabilities)]
    return classified_tiles

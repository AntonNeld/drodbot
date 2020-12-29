import os
import os.path
import random
import string

import PIL
from PIL.PngImagePlugin import PngInfo

from common import ImageProcessingStep, Element, Direction, Room


class ClassificationTrainer:
    def __init__(self, training_data_dir, drod_interface):
        self._training_data_dir = training_data_dir
        self._interface = drod_interface

    async def procure_training_data(self):
        """Generate data for training the classification model.

        With the editor open, this method will add elements to the room
        with various floors, and save the tiles as images.
        The images are annotated with the tile contents as metadata.

        Work in progress.
        """
        print("Generating training data")
        await self._interface.initialize(editor=True)
        await self._interface.editor_clear_room()
        room = Room()
        # TODO: place elements in a more representative way
        await self._interface.editor_place_element(
            Element.WALL, Direction.NONE, (5, 5), (6, 8)
        )
        room.place_element_like_editor(Element.WALL, Direction.NONE, (5, 5), (6, 8))
        await self._interface.editor_place_element(
            Element.CONQUER_TOKEN, Direction.NONE, (10, 20)
        )
        room.place_element_like_editor(Element.CONQUER_TOKEN, Direction.NONE, (10, 20))
        await self._interface.editor_place_element(
            Element.BEETHRO, Direction.NE, (11, 20)
        )
        room.place_element_like_editor(Element.BEETHRO, Direction.NE, (11, 20))

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

import os
import os.path
import random
import string

import PIL
from PIL.PngImagePlugin import PngInfo

from common import ImageProcessingStep, Element, Direction, Tile


class ClassificationTrainer:
    def __init__(self, training_data_dir, drod_interface):
        self._training_data_dir = training_data_dir
        self._interface = drod_interface

    async def procure_training_data(self):
        """Generate data for training the classification model.

        With the editor open, this method will add elements to the room
        with various floors, and save the tiles as images with random names.
        The images are annotated with the tile contents as metadata.

        Work in progress.
        """
        await self._interface.initialize()
        await self._interface.editor_clear_room()
        # TODO: place some elements, and keep track of where
        await self._interface.editor_place_element(Element.WALL, (5, 5), (6, 8))
        await self._interface.editor_place_element(Element.CONQUER_TOKEN, (10, 20))

        visual_info = await self._interface.get_view(
            step=ImageProcessingStep.EXTRACT_TILES
        )
        if not os.path.exists(self._training_data_dir):
            os.makedirs(self._training_data_dir)
        for coords, tile in visual_info["tiles"].items():
            # Annotate the image with the tile contents
            # Temporary tile contents for now.
            tile_info = Tile(
                room_piece=(Element.FLOOR, Direction.NONE),
                monster=(Element.BEETHRO, Direction.W),
                swords=[
                    (Element.WALL, Direction.NW),
                    (Element.CONQUER_TOKEN, Direction.E),
                ],
            )
            png_info = PngInfo()
            png_info.add_text("tile_json", tile_info.to_json())
            # Save the image with a random name
            image = PIL.Image.fromarray(tile)
            random_string = "".join(
                random.choices(string.ascii_uppercase + string.digits, k=5)
            )
            image.save(
                os.path.join(
                    self._training_data_dir,
                    f"{random_string}.png",
                ),
                "PNG",
                pnginfo=png_info,
            )

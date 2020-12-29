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
        await self._interface.initialize(editor=True)
        await self._interface.editor_clear_room()
        room = Room()
        # TODO: place elements in a more representative way
        await self._interface.editor_place_element(Element.WALL, (5, 5), (6, 8))
        room.place_element_like_editor(Element.WALL, Direction.NONE, (5, 5), (6, 8))
        await self._interface.editor_place_element(Element.CONQUER_TOKEN, (10, 20))
        room.place_element_like_editor(Element.CONQUER_TOKEN, Direction.NONE, (10, 20))
        await self._interface.editor_place_element(Element.BEETHRO, (11, 20))
        room.place_element_like_editor(Element.BEETHRO, Direction.SE, (11, 20))

        visual_info = await self._interface.get_view(
            step=ImageProcessingStep.EXTRACT_TILES
        )

        if not os.path.exists(self._training_data_dir):
            os.makedirs(self._training_data_dir)
        random_string = "".join(
            random.choices(string.ascii_uppercase + string.digits, k=5)
        )
        for coords, tile in visual_info["tiles"].items():
            # Annotate the image with the tile contents
            # Temporary tile contents for now.
            tile_info = room.get_tile(coords)
            png_info = PngInfo()
            png_info.add_text("tile_json", tile_info.to_json())
            # Save the image with a random name
            image = PIL.Image.fromarray(tile)
            image.save(
                os.path.join(
                    self._training_data_dir,
                    f"{random_string}_{coords[0]}_{coords[1]}.png",
                ),
                "PNG",
                pnginfo=png_info,
            )

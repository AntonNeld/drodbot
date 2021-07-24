import json
import os
import os.path
import shutil

import numpy
import PIL
from PIL.PngImagePlugin import PngInfo

from common import GUIEvent, ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES, TILE_SIZE
from room_simulator import ElementType, Direction
from tile_classifier import ApparentTile
from .editor_utils import (
    place_fully_directional_elements,
    place_nondirectional_edges_elements,
    place_rectangle,
    place_sized_obstacles,
    place_sworded_element,
)
from util import element_layer


class ClassificationAppBackend:
    """The backend for the classification app.

    It generates tile data for the classifier, and sample data to
    test it.

    Parameters
    ----------
    classifier
        The classifier.
    tile_data_dir
        The directory to put tile data in.
    sample_data_dir
        The directory to read and write sample data.
    editor_interface
        The interface to the DROD editor, to generate data.
    window_queue
        A queue for sending updates to the GUI.
    """

    def __init__(
        self, classifier, tile_data_dir, sample_data_dir, editor_interface, window_queue
    ):
        self._tile_data_dir = tile_data_dir
        self._sample_data_dir = sample_data_dir
        self._interface = editor_interface
        self._sample_data = []
        self._queue = window_queue
        self._classifier = classifier

    async def load_sample_data(self):
        """Load the sample data and send it to the GUI."""
        print("Loading sample data...")
        self._sample_data = []
        try:
            file_names = os.listdir(self._sample_data_dir)
        except FileNotFoundError:
            print("No sample data directory found")
            self._queue.put((GUIEvent.SET_CLASSIFICATION_DATA, self._sample_data))
            return
        for file_name in file_names:
            image = PIL.Image.open(os.path.join(self._sample_data_dir, file_name))
            content = ApparentTile.parse_raw(image.info["tile_json"])
            minimap_color = tuple(json.loads(image.info["minimap_color"]))
            x = int(image.info["x"])
            y = int(image.info["y"])
            self._sample_data.append(
                {
                    "image": numpy.array(image),
                    "real_content": content,
                    "file_name": file_name,
                    "minimap_color": minimap_color,
                    "position": (x, y),
                }
            )
        print("Classifying sample data...")
        self._classify_sample_data()
        self._queue.put((GUIEvent.SET_CLASSIFICATION_DATA, self._sample_data))
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
            ElementType.FLOOR, Direction.NONE, (0, 0), (37, 31), style="image"
        )

        tile_collections = []
        elements = []
        whole_room_images = []
        print("Getting elements that don't depend on room style...")
        unstyled_elements = await self._make_unstyled_tile_data_room()
        await self._interface.start_test_room((37, 31), Direction.SE)
        tiles, _ = await self._interface.get_tiles_and_colors()
        await self._interface.stop_test_room()
        tile_collections.append(tiles)
        elements.extend([(*element, 0) for element in unstyled_elements])

        await self._interface.clear_room()
        await self._interface.place_element(
            ElementType.FLOOR, Direction.NONE, (0, 0), (37, 31), style="image"
        )
        print("Getting elements that depend on room style...")
        styled_elements = await self._make_styled_tile_data_room()
        await self._interface.start_test_room((37, 31), Direction.SE)
        tiles, _ = await self._interface.get_tiles_and_colors()
        await self._interface.stop_test_room()
        tile_collections.append(tiles)
        elements.extend((*element, 1) for element in styled_elements)

        await self._interface.clear_room()
        print("Getting whole-room images...")
        for (element, style) in [
            (ElementType.FLOOR, None),
            (ElementType.FLOOR, "mosaic"),
            (ElementType.FLOOR, "road"),
            (ElementType.FLOOR, "grass"),
            (ElementType.FLOOR, "dirt"),
            (ElementType.FLOOR, "alternate"),
            (ElementType.PIT, None),
            (ElementType.WALL, None),
        ]:
            await self._interface.place_element(
                element, Direction.NONE, (0, 0), (37, 31), style=style
            )
            await self._interface.start_test_room((37, 31), Direction.SE)
            room_image = await self._interface.get_room_image()
            await self._interface.stop_test_room()
            if element != ElementType.FLOOR:
                await self._interface.clear_room()
            whole_room_images.append((element, style, _fix_corner_tiles(room_image)))

        print("Making tile data files...")
        if os.path.exists(self._tile_data_dir):
            shutil.rmtree(self._tile_data_dir)
        os.makedirs(self._tile_data_dir)
        used_names = []
        for (element, direction, x, y, style, tile_collection_index) in elements:
            png_info = PngInfo()
            png_info.add_text("element", element.name)
            png_info.add_text("direction", direction.name)
            image = PIL.Image.fromarray(tile_collections[tile_collection_index][(x, y)])
            direction_str = f"_{direction.name}" if direction != Direction.NONE else ""
            style_str = f"_{style}" if style is not None else ""
            base_name = f"{element.name}{direction_str}{style_str}"
            name_increment = 0
            while base_name in used_names:
                base_name = f"{element.name}{direction_str}{style_str}_{name_increment}"
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
        os.makedirs(os.path.join(self._tile_data_dir, "whole_room_images"))
        for (element, style, room_image) in whole_room_images:
            png_info = PngInfo()
            png_info.add_text("element", element.name)
            image = PIL.Image.fromarray(room_image)
            style_str = f"_{style}" if style is not None else ""
            file_name = f"{element.name}{style_str}"
            image.save(
                os.path.join(
                    os.path.join(self._tile_data_dir, "whole_room_images"),
                    f"{file_name}.png",
                ),
                "PNG",
                pnginfo=png_info,
            )

        # Classify tiles once done
        self._classifier.load_tile_data(self._tile_data_dir)
        if self._sample_data:
            self._classify_sample_data()
            self._queue.put((GUIEvent.SET_CLASSIFICATION_DATA, self._sample_data))
        print("Finished getting tile data")

    async def _make_styled_tile_data_room(self):
        # Place some walls we don't care about, to make shadows for force arrows
        await place_rectangle(self._interface, ElementType.WALL, 20, 13, 9, 1)
        elements = (
            await place_fully_directional_elements(
                self._interface, ElementType.FORCE_ARROW, 8, 2
            )
            + await place_nondirectional_edges_elements(
                self._interface, ElementType.WALL, 1, 4, "hard"
            )
            + await place_sized_obstacles(self._interface, "rock_1", 7, 0, [1, 2, 3])
            + await place_sized_obstacles(self._interface, "rock_2", 11, 4, [1, 2, 3])
            + await place_sized_obstacles(
                self._interface, "square_statue", 16, 1, [1, 2, 4]
            )
            # Place some force arrows in the shadow, since we're having trouble seeing
            # those otherwise
            + await place_fully_directional_elements(
                self._interface, ElementType.FORCE_ARROW, 21, 14, one_line=True
            )
            + await place_rectangle(self._interface, ElementType.PIT, 20, 15, 5, 4)
            + await place_rectangle(self._interface, ElementType.STAIRS, 34, 5, 1, 19)
            + await place_rectangle(
                self._interface, ElementType.STAIRS, 35, 5, 1, 19, style="up"
            )
        )
        return elements

    async def _make_unstyled_tile_data_room(self):
        elements = (
            await place_sworded_element(
                self._interface,
                ElementType.BEETHRO,
                ElementType.BEETHRO_SWORD,
                0,
                0,
            )
            + await place_fully_directional_elements(
                self._interface, ElementType.ROACH, 0, 3
            )
            + await place_nondirectional_edges_elements(
                self._interface, ElementType.YELLOW_DOOR, 1, 9
            )
            + await place_nondirectional_edges_elements(
                self._interface, ElementType.BLUE_DOOR, 1, 14
            )
            + await place_nondirectional_edges_elements(
                self._interface, ElementType.GREEN_DOOR, 1, 19
            )
            + await place_nondirectional_edges_elements(
                self._interface, ElementType.YELLOW_DOOR_OPEN, 11, 9
            )
            + await place_nondirectional_edges_elements(
                self._interface, ElementType.BLUE_DOOR_OPEN, 11, 14
            )
            + await place_nondirectional_edges_elements(
                self._interface, ElementType.GREEN_DOOR_OPEN, 11, 19
            )
        )
        extra_elements = [
            (ElementType.CONQUER_TOKEN, Direction.NONE, 0, 5, None),
            (ElementType.MASTER_WALL, Direction.NONE, 4, 3, None),
            (ElementType.ORB, Direction.NONE, 6, 1, None),
            (ElementType.CHECKPOINT, Direction.NONE, 7, 1, None),
            (ElementType.SCROLL, Direction.NONE, 12, 3, None),
        ]
        for (element, direction, x, y, style) in extra_elements:
            await self._interface.place_element(element, direction, (x, y), style=style)
        elements.extend(extra_elements)

        return elements

    def _classify_sample_data(self):
        """Classify the loaded sample data."""
        predicted_contents, debug_images = self._classifier.classify_tiles(
            {t["position"]: t["image"] for t in self._sample_data},
            {t["position"]: t["minimap_color"] for t in self._sample_data},
            return_debug_images=True,
        )
        for entry in self._sample_data:
            entry["predicted_content"] = predicted_contents[entry["position"]]
            entry["debug_images"] = debug_images[entry["position"]]

    async def generate_sample_data(self):
        """Generate some sample data to test the classifier."""
        print("Generating sample data...")
        await self._interface.initialize()
        await self._interface.clear_room()

        elements = await place_rectangle(self._interface, ElementType.WALL, 5, 10, 6, 6)
        extra_elements = [
            (ElementType.FLOOR, Direction.NONE, 0, 0, None),
            (ElementType.BEETHRO, Direction.N, 0, 1, None),
            (ElementType.BEETHRO, Direction.N, 0, 2, None),
            (ElementType.BEETHRO, Direction.NE, 1, 1, None),
            (ElementType.FLOOR, Direction.NONE, 2, 1, None),
            (ElementType.BEETHRO, Direction.NW, 3, 1, None),
            (ElementType.ROACH, Direction.N, 2, 0, None),
            (ElementType.ROACH, Direction.NE, 3, 3, None),
            (ElementType.ROACH, Direction.SW, 3, 4, None),
            (ElementType.GREEN_DOOR_OPEN, Direction.NONE, 5, 5, None),
            (ElementType.ROACH, Direction.SE, 5, 5, None),
            (ElementType.WALL, Direction.NONE, 12, 25, None),
            (ElementType.WALL, Direction.NONE, 13, 25, None),
            (ElementType.WALL, Direction.NONE, 13, 24, None),
            (ElementType.WALL, Direction.NONE, 11, 26, None),
            (ElementType.WALL, Direction.NONE, 12, 26, None),
            (ElementType.FLOOR, Direction.NONE, 11, 27, None),
            (ElementType.FLOOR, Direction.NONE, 12, 27, None),
            (ElementType.FLOOR, Direction.NONE, 13, 27, None),
            (ElementType.FLOOR, Direction.NONE, 13, 26, None),
            (ElementType.FLOOR, Direction.NONE, 14, 25, None),
            (ElementType.FLOOR, Direction.NONE, 14, 24, None),
            (ElementType.WALL, Direction.NONE, 15, 23, None),
            (ElementType.WALL, Direction.NONE, 16, 22, None),
            (ElementType.FLOOR, Direction.NONE, 16, 23, None),
            (ElementType.BLUE_DOOR, Direction.NONE, 6, 5, None),
            (ElementType.BLUE_DOOR, Direction.NONE, 7, 5, None),
            (ElementType.BLUE_DOOR, Direction.NONE, 8, 5, None),
            (ElementType.BLUE_DOOR, Direction.NONE, 6, 6, None),
            (ElementType.BLUE_DOOR, Direction.NONE, 7, 6, None),
            (ElementType.BLUE_DOOR, Direction.NONE, 8, 6, None),
            (ElementType.BLUE_DOOR, Direction.NONE, 6, 7, None),
            (ElementType.BLUE_DOOR, Direction.NONE, 7, 7, None),
            (ElementType.BLUE_DOOR, Direction.NONE, 8, 7, None),
            (ElementType.OBSTACLE, Direction.NONE, 28, 5, None),
            (ElementType.FORCE_ARROW, Direction.NW, 9, 9, None),
            (ElementType.FLOOR, Direction.NONE, 7, 16, "road"),
            (ElementType.FORCE_ARROW, Direction.W, 7, 16, None),
        ]
        for (element, direction, x, y, style) in extra_elements:
            await self._interface.place_element(element, direction, (x, y), style=style)

        elements.extend(extra_elements)

        await self._interface.start_test_room((37, 31), Direction.SE)
        tiles, colors = await self._interface.get_tiles_and_colors()
        await self._interface.stop_test_room()

        # Assign elements to tiles
        tile_contents = {}
        for (element, direction, x, y, style) in elements:
            if (x, y) not in tile_contents:
                tile_contents[(x, y)] = ApparentTile(
                    room_piece=(ElementType.FLOOR, Direction.NONE)
                )
            layer = element_layer(element)
            if layer == "room_piece":
                tile_contents[(x, y)].room_piece = (element, direction)
            elif layer == "floor_control":
                tile_contents[(x, y)].floor_control = (element, direction)
            elif layer == "checkpoint":
                tile_contents[(x, y)].checkpoint = (element, direction)
            elif layer == "item":
                tile_contents[(x, y)].item = (element, direction)
            elif layer == "monster":
                tile_contents[(x, y)].monster = (element, direction)
        if os.path.exists(self._sample_data_dir):
            shutil.rmtree(self._sample_data_dir)
        os.makedirs(self._sample_data_dir)
        for (x, y), tile_info in tile_contents.items():
            minimap_color = colors[(x, y)]
            png_info = PngInfo()
            png_info.add_text("tile_json", tile_info.json())
            png_info.add_text("x", str(x))
            png_info.add_text("y", str(y))
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


def _fix_corner_tiles(room_image):
    """Remove Beethro from the corner tile.

    Since the textures are periodic, we can remove Beethro
    from the bottom-right tile by replacing him with another
    tile from the room image.

    Parameters
    ----------
    room_image
        The room image.

    Returns
    -------
    The fixed room image.
    """
    match_region_size = 3
    replace_region_size = 2  # Beethro is drawn in multiple tiles when on a wall
    # Cut out a region to match with, just above the corner
    region_to_match = room_image[
        (ROOM_HEIGHT_IN_TILES - replace_region_size - match_region_size)
        * TILE_SIZE : (ROOM_HEIGHT_IN_TILES - replace_region_size)
        * TILE_SIZE,
        (ROOM_WIDTH_IN_TILES - match_region_size)
        * TILE_SIZE : ROOM_WIDTH_IN_TILES
        * TILE_SIZE,
        :,
    ]
    # Find all matches
    matching_origins = []
    for x in range(ROOM_WIDTH_IN_TILES - match_region_size):
        for y in range(ROOM_HEIGHT_IN_TILES - match_region_size - replace_region_size):
            if (
                x == ROOM_WIDTH_IN_TILES - match_region_size
                and y == ROOM_HEIGHT_IN_TILES - match_region_size - replace_region_size
            ):
                # Skip the region we just extracted, since Beethro is below it
                continue
            if (
                region_to_match
                == room_image[
                    y * TILE_SIZE : (y + match_region_size) * TILE_SIZE,
                    x * TILE_SIZE : (x + match_region_size) * TILE_SIZE,
                    :,
                ]
            ).all():
                matching_origins.append((x, y))
    # Extract tiles to replace
    replacements = [
        room_image[
            (y + match_region_size)
            * TILE_SIZE : (y + match_region_size + replace_region_size)
            * TILE_SIZE,
            (x + match_region_size - replace_region_size)
            * TILE_SIZE : (x + match_region_size)
            * TILE_SIZE,
            :,
        ]
        for (x, y) in matching_origins
    ]
    # Verify that they are all identical
    replacement = replacements[0]
    for other_replacement in replacements[1:]:
        if not (replacement == other_replacement).all():
            raise RuntimeError("Not all replacements are identical")
    # Replace Beethro with the found replacement
    fixed_room_image = room_image.copy()
    fixed_room_image[
        (ROOM_HEIGHT_IN_TILES - replace_region_size)
        * TILE_SIZE : ROOM_HEIGHT_IN_TILES
        * TILE_SIZE,
        (ROOM_WIDTH_IN_TILES - replace_region_size)
        * TILE_SIZE : ROOM_WIDTH_IN_TILES
        * TILE_SIZE,
        :,
    ] = replacement
    return fixed_room_image

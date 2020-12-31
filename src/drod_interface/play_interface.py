import numpy
import pyautogui

from common import (
    ROOM_WIDTH_IN_TILES,
    ROOM_HEIGHT_IN_TILES,
    TILE_SIZE,
    Action,
    GUIEvent,
    ImageProcessingStep,
    Room,
)
from .classify import classify_tile
from .util import get_drod_window

ROOM_ORIGIN_X = 163
ROOM_ORIGIN_Y = 40


class PlayInterface:
    def __init__(self, window_queue):
        self._queue = window_queue
        # Will be set by initialize()
        self.origin_x = None
        self.origin_y = None

    async def initialize(self):
        """Find the DROD window and focus it.

        This should be done before each user-triggered action, as the
        window will have lost focus.
        """
        origin_x, origin_y, _ = await get_drod_window()
        self.origin_x = origin_x
        self.origin_y = origin_y
        await self._click((3, 3))

    async def _click(self, position):
        pyautogui.click(x=self.origin_x + position[0], y=self.origin_y + position[1])

    async def do_action(self, action):
        if action == Action.SW:
            key = "num1"
        elif action == Action.S:
            key = "num2"
        elif action == Action.SE:
            key = "num3"
        elif action == Action.W:
            key = "num4"
        elif action == Action.WAIT:
            key = "num5"
        elif action == Action.E:
            key = "num6"
        elif action == Action.NW:
            key = "num7"
        elif action == Action.N:
            key = "num8"
        elif action == Action.NE:
            key = "num9"
        elif action == Action.CCW:
            key = "q"
        elif action == Action.CW:
            key = "w"
        pyautogui.press(key)

    async def get_view(self, step=None):
        visual_info = {}
        if step in [
            ImageProcessingStep.SCREENSHOT,
            ImageProcessingStep.FIND_UPPER_EDGE_COLOR,
            ImageProcessingStep.FIND_UPPER_EDGE_LINE,
        ]:
            _, _, image = await get_drod_window(stop_after=step)
            visual_info["image"] = image
            return visual_info
        origin_x, origin_y, image = await get_drod_window()
        visual_info["origin_x"] = origin_x
        visual_info["origin_y"] = origin_y
        if step == ImageProcessingStep.CROP_WINDOW:
            visual_info["image"] = image
            return visual_info

        room_end_x = ROOM_ORIGIN_X + ROOM_WIDTH_IN_TILES * TILE_SIZE
        room_end_y = ROOM_ORIGIN_Y + ROOM_HEIGHT_IN_TILES * TILE_SIZE
        room_image = image[ROOM_ORIGIN_Y:room_end_y, ROOM_ORIGIN_X:room_end_x, :]

        if step == ImageProcessingStep.CROP_ROOM:
            visual_info["image"] = room_image
            return visual_info

        # == Extract and classify tiles in the room ==

        tiles = {}
        for x in range(ROOM_WIDTH_IN_TILES):
            for y in range(ROOM_HEIGHT_IN_TILES):
                start_x = x * TILE_SIZE
                end_x = (x + 1) * TILE_SIZE
                start_y = y * TILE_SIZE
                end_y = (y + 1) * TILE_SIZE
                tiles[(x, y)] = room_image[start_y:end_y, start_x:end_x, :]
        visual_info["tiles"] = tiles

        if step == ImageProcessingStep.EXTRACT_TILES:
            # We can't show anything more interesting here
            visual_info["image"] = room_image
            return visual_info

        # If a step is specified, we will return an image composed of modified tiles
        if step == ImageProcessingStep.AVERAGE_TILE_COLOR:
            averaged_room = numpy.zeros(room_image.shape, numpy.uint8)
        room = Room()
        for (x, y), tile in tiles.items():
            start_x = x * TILE_SIZE
            end_x = (x + 1) * TILE_SIZE
            start_y = y * TILE_SIZE
            end_y = (y + 1) * TILE_SIZE
            tile_info, modified_tile = classify_tile(tile, step)
            if step == ImageProcessingStep.AVERAGE_TILE_COLOR:
                averaged_room[start_y:end_y, start_x:end_x] = modified_tile
            else:
                room.set_tile((x, y), tile_info)

        if step == ImageProcessingStep.AVERAGE_TILE_COLOR:
            visual_info["image"] = averaged_room
            return visual_info

        visual_info["room"] = room

        # If no earlier step is specified, include the normal room image
        visual_info["image"] = room_image
        return visual_info

    async def show_view_step(self, step):
        """Show the given view step in the GUI.

        This method will add the image and room to the window queue.

        Parameters
        ----------
        step
            The step to stop at.
        """
        visual_info = await self.get_view(step)
        self._queue.put(
            (
                GUIEvent.SET_INTERPRET_SCREEN_DATA,
                visual_info["image"],
                visual_info["room"] if "room" in visual_info else None,
            )
        )

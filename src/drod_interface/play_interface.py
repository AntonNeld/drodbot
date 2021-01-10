import pyautogui

from common import (
    Action,
    ImageProcessingStep,
    Room,
)
from .util import (
    get_drod_window,
    extract_room,
    extract_minimap,
    extract_tiles,
)


class PlayInterface:
    """The interface toward DROD when playing the game.

    Parameters
    ----------
    window_queue
        A queue for sending updates to the GUI.
    classifier
        The tile classifier, to interpret the tiles.
    """

    def __init__(self, window_queue, classifier):
        self._queue = window_queue
        self._classifier = classifier
        # Will be set by initialize()
        self._origin_x = None
        self._origin_y = None

    async def initialize(self):
        """Find the DROD window and focus it.

        This should be done before each user-triggered action, as the
        window will have lost focus.
        """
        origin_x, origin_y, _ = await get_drod_window()
        self._origin_x = origin_x
        self._origin_y = origin_y
        await self._click((3, 3))

    async def _click(self, position):
        pyautogui.click(x=self._origin_x + position[0], y=self._origin_y + position[1])

    async def do_action(self, action):
        """Perform an action, like moving or swinging your sword.

        Parameters
        ----------
        action
            The action to perform.
        """
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
        """Get the room contents and other information from the DROD window.

        Parameters
        ----------
        step
            If given, stop at this step and return an intermediate image.

        Returns
        -------
        A dict containing the following keys:
        - "image": The room image or intermediate image
        - "origin_x": The X coordinate of the upper left corner of the window
        - "origin_y": The Y coordinate of the upper left corner of the window
        - "tiles": A dict mapping (x, y) coordinates to tile images
        - "room": A representation of the room, interpreted from the screenshot
        Not all keys may be present if `step` is given.
        """
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

        room_image = extract_room(image)

        if step == ImageProcessingStep.CROP_ROOM:
            visual_info["image"] = room_image
            return visual_info

        minimap = extract_minimap(image)

        if step == ImageProcessingStep.EXTRACT_MINIMAP:
            visual_info["image"] = minimap
            return visual_info

        # == Extract and classify tiles in the room ==

        tiles, minimap_colors = extract_tiles(room_image, minimap)
        visual_info["tiles"] = tiles

        if step == ImageProcessingStep.EXTRACT_TILES:
            # We can't show anything more interesting here
            visual_info["image"] = room_image
            return visual_info

        tile_contents = self._classifier.classify_tiles(tiles, minimap_colors)
        room = Room()
        for coords, tile in tile_contents.items():
            room.set_tile(coords, tile)
        visual_info["room"] = room

        # If no earlier step is specified, include the normal room image
        visual_info["image"] = room_image
        return visual_info

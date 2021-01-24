import pyautogui

from common import (
    Action,
    ImageProcessingStep,
    TILE_SIZE,
)
from .consts import ROOM_ORIGIN_X, ROOM_ORIGIN_Y
from room import ElementType
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
    classifier
        The tile classifier, to interpret the tiles.
    """

    def __init__(self, classifier):
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

    async def _click_tile(self, position):
        x, y = position
        await self._click(
            (
                ROOM_ORIGIN_X + (x + 0.5) * TILE_SIZE,
                ROOM_ORIGIN_Y + (y + 0.5) * TILE_SIZE,
            )
        )

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
        visual_info["tile_contents"] = tile_contents

        orb_positions = [
            pos
            for pos, tile in tile_contents.items()
            if tile.item[0] == ElementType.ORB
        ]
        # A position we can click to get rid of the displayed orb effects
        # TODO: Handle the case when there is no such position
        free_position = next(
            pos
            for pos, tile in tile_contents.items()
            if tile.item[0] != ElementType.ORB
            and tile.room_piece[0]
            not in [ElementType.YELLOW_DOOR, ElementType.YELLOW_DOOR_OPEN]
        )
        visual_info["orb_effects"] = await self._get_orb_effects(
            orb_positions, room_image, free_position
        )

        # If no earlier step is specified, include the normal room image
        visual_info["image"] = room_image
        return visual_info

    async def _get_orb_effects(self, positions, original_room_image, free_position):
        """Get the orb effects for the given positions.

        Parameters
        ----------
        positions
            The positions to get effects of.
        original_room_image
            The room image without clicking anything.
        free_position
            A free position we can click to restore the view to one without effects.

        Returns
        -------
        A dict mapping positions to lists of orb effects
        """
        orb_effects = {}
        for position in positions:
            await self._click_tile(position)
            # TODO: Compare room image to original room image to find orb effects
            orb_effects[position] = []
        # Click somewhere else to go back to the normal view
        await self._click_tile(free_position)
        return orb_effects

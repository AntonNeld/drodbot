import numpy
import pyautogui
from common import (
    Action,
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

    async def get_view(self, return_debug_images=False):
        """Get the room contents and other information from the DROD window.

        Parameters
        ----------
        return_debug_images
            If True, return an additional list of tuples (name, debug_image).

        Returns
        -------
        tile_contents
            A dict mapping all coordinates to apparent tiles.
        orb_effects
            A dict mapping some coordinates to orb effects.
        debug_images
            Only returned if `return_debug_images` is True. A list of (name, image).
        """
        if return_debug_images:
            debug_images = []

        if return_debug_images:
            origin_x, origin_y, image, window_debug_images = await get_drod_window(
                return_debug_images=True
            )
            debug_images.extend(window_debug_images)
            debug_images.append(("Extract DROD window", image))
        else:
            origin_x, origin_y, image = await get_drod_window()

        room_image = extract_room(image)
        if return_debug_images:
            debug_images.append(("Extract room", room_image))

        minimap = extract_minimap(image)
        if return_debug_images:
            debug_images.append(("Extract minimap", minimap))

        # == Extract and classify tiles in the room ==

        tiles, minimap_colors = extract_tiles(room_image, minimap)

        tile_contents = self._classifier.classify_tiles(tiles, minimap_colors)

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
        if return_debug_images:
            orb_effects, effects_debug_images = await self._get_orb_effects(
                orb_positions, room_image, free_position, return_debug_images=True
            )
            debug_images.extend(effects_debug_images)
        else:
            orb_effects = await self._get_orb_effects(
                orb_positions, room_image, free_position
            )

        if return_debug_images:
            return tile_contents, orb_effects, debug_images
        return tile_contents, orb_effects

    async def _get_orb_effects(
        self, positions, original_room_image, free_position, return_debug_images=False
    ):
        """Get the orb effects for the given positions.

        Parameters
        ----------
        positions
            The positions to get effects of.
        original_room_image
            The room image without clicking anything.
        free_position
            A free position we can click to restore the view to one without effects.
        return_debug_images
            Whether to return debug images.

        Returns
        -------
        A dict mapping positions to lists of orb effects. If `return_debug_images`
        if True, also return a list of (name, image).
        """
        orb_effects = {}
        if return_debug_images:
            debug_images = []
        for position in positions:
            await self._click_tile(position)
            _, _, window_image = await get_drod_window()
            room_image = extract_room(window_image).astype(float)
            if return_debug_images:
                debug_images.append(
                    (
                        f"Orb effects screenshot {position}",
                        room_image.astype(numpy.uint8),
                    )
                )
            orb_effects[position] = []
        # Click somewhere else to go back to the normal view
        await self._click_tile(free_position)
        if return_debug_images:
            return orb_effects, debug_images
        return orb_effects

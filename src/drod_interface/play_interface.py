import numpy
import pyautogui
import scipy.ndimage
from common import Action, TILE_SIZE, ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from .consts import ROOM_ORIGIN_X, ROOM_ORIGIN_Y
from room_simulator import ElementType, OrbEffect
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
        averaged_original = _average_tiles(original_room_image.astype(float))
        if return_debug_images:
            debug_images.append(
                ("Averaged room image", averaged_original.astype(numpy.uint8))
            )
        for position in positions:
            await self._click_tile(position)
            _, _, window_image = await get_drod_window()
            room_image = extract_room(window_image).astype(float)
            averaged_room = _average_tiles(room_image)
            diff = numpy.sqrt(
                numpy.sum((averaged_room - averaged_original) ** 2, axis=-1)
            )
            affected_tiles = diff > 10
            if return_debug_images:
                debug_images.extend(
                    [
                        (
                            f"Orb effects screenshot {position}",
                            room_image.astype(numpy.uint8),
                        ),
                        (
                            f"Orb effects averaged screenshot {position}",
                            averaged_room.astype(numpy.uint8),
                        ),
                        (f"Orb effects diff {position}", diff.astype(numpy.uint8)),
                        (
                            f"Orb affected tiles {position}",
                            affected_tiles,
                        ),
                    ]
                )

            # If affected tiles belong to the same door, only one of the tiles
            # is a target for the orb. We can't know which one, but it doesn't
            # matter.
            labels, num_labels = scipy.ndimage.label(affected_tiles)
            effect_targets = numpy.zeros(affected_tiles.shape, dtype=bool)
            for i in range(1, num_labels + 1):
                coords = numpy.argwhere(labels == i)[0]
                effect_targets[coords[0], coords[1]] = True
            if return_debug_images:
                debug_images.append(
                    (f"Orb effect regions {position}", labels * 255 // num_labels)
                )
                debug_images.append((f"Orb effect targets {position}", effect_targets))

            if return_debug_images:
                recovered_highlights = numpy.zeros(averaged_room.shape)
                determined_effects = numpy.zeros(averaged_room.shape)
            orb_effects[position] = []
            for coords in numpy.argwhere(effect_targets):
                # Convert to int so we can save the coordinates in orb_effects
                y = int(coords[0])
                x = int(coords[1])
                # Recover the source using the background and the result,
                # given the alpha blending equation
                # result = source*alpha + background*(1-alpha)
                # with alpha=0.5
                color = 2 * averaged_room[y, x] - averaged_original[y, x]
                if return_debug_images:
                    recovered_highlights[y, x] = color
                if numpy.linalg.norm(color - [255, 0, 64]) < 10:
                    if return_debug_images:
                        determined_effects[y, x] = [255, 0, 64]
                    orb_effects[position].append((x, y, OrbEffect.CLOSE))
                elif numpy.linalg.norm(color - [255, 128, 0]) < 10:
                    if return_debug_images:
                        determined_effects[y, x] = [255, 128, 0]
                    orb_effects[position].append((x, y, OrbEffect.TOGGLE))
                elif numpy.linalg.norm(color - [0, 255, 255]) < 10:
                    if return_debug_images:
                        determined_effects[y, x] = [0, 255, 255]
                    orb_effects[position].append((x, y, OrbEffect.OPEN))
            if return_debug_images:
                recovered_highlights[recovered_highlights < 0] = 0
                recovered_highlights[recovered_highlights > 255] = 255
                debug_images.extend(
                    [
                        (
                            f"Recovered highlights {position}",
                            recovered_highlights.astype(numpy.uint8),
                        ),
                        (
                            f"Determined effects {position}",
                            determined_effects.astype(numpy.uint8),
                        ),
                    ]
                )

        # Click somewhere else to go back to the normal view
        await self._click_tile(free_position)
        if return_debug_images:
            return orb_effects, debug_images
        return orb_effects


def _average_tiles(room_image):
    height, width, colors = room_image.shape
    return room_image.reshape(
        (
            ROOM_HEIGHT_IN_TILES,
            height // ROOM_HEIGHT_IN_TILES,
            ROOM_WIDTH_IN_TILES,
            width // ROOM_WIDTH_IN_TILES,
            colors,
        )
    ).mean((1, 3))

import numpy
import pyautogui
import scipy.ndimage
from PIL import Image, ImageFont, ImageDraw
from common import TILE_SIZE, ROOM_HEIGHT_IN_TILES, ROOM_WIDTH_IN_TILES
from .consts import ROOM_ORIGIN_X, ROOM_ORIGIN_Y
from room_simulator import OrbEffect, Action
from util import find_color
from .util import get_drod_window, extract_room, extract_minimap

# These are lovingly hand-copied from screenshots.
# The font is called "Tom's New Roman" and can be found here:
# https://www.1001fonts.com/toms-new-roman-font.html

_HASH_PATTERN = numpy.array(
    [
        [0, 0, 1, 1, 0, 0, 0, 1],
        [0, 0, 1, 1, 0, 0, 1, 1],
        [0, 0, 1, 1, 0, 0, 1, 1],
        [0, 0, 1, 1, 0, 1, 1, 0],
        [0, 1, 1, 0, 0, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [0, 1, 1, 0, 0, 1, 1, 0],
        [0, 1, 1, 0, 0, 1, 1, 0],
        [1, 1, 1, 1, 1, 1, 1, 1],
        [0, 1, 0, 0, 1, 1, 0, 0],
        [1, 1, 0, 0, 1, 1, 0, 0],
        [1, 1, 0, 0, 1, 1, 0, 0],
        [1, 1, 0, 0, 1, 1, 0, 0],
    ]
)

_NUMBER_PATTERNS = {
    0: numpy.array(
        [
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 0, 0, 1, 1, 0],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 1, 0],
        ]
    ),
    1: numpy.array(
        [
            [0, 1, 1, 0],
            [1, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [0, 1, 1, 0],
            [1, 1, 1, 1],
        ]
    ),
    2: numpy.array(
        [
            [0, 0, 0, 1, 1, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [1, 1, 1, 1, 1, 1, 1, 0],
            [1, 1, 0, 0, 0, 1, 1, 0],
            [1, 0, 0, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 1, 1, 1, 0],
            [0, 0, 0, 1, 1, 1, 0, 0],
            [0, 0, 1, 1, 1, 0, 0, 1],
            [0, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1],
        ]
    ),
    3: numpy.array(
        [
            [0, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 0, 0, 1, 1, 1],
            [0, 0, 0, 0, 1, 1, 1],
            [0, 0, 0, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 0],
            [0, 0, 0, 1, 1, 1, 1],
            [0, 0, 0, 0, 1, 1, 1],
            [0, 0, 0, 0, 0, 1, 1],
            [0, 0, 0, 0, 0, 1, 1],
            [1, 1, 1, 0, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 0],
        ]
    ),
    4: numpy.array(
        [
            [0, 0, 0, 0, 1, 1, 1, 0],
            [0, 0, 0, 0, 1, 1, 1, 0],
            [0, 0, 0, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 0, 1, 1, 0],
            [0, 1, 1, 0, 0, 1, 1, 0],
            [0, 1, 1, 0, 0, 1, 1, 0],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
        ]
    ),
    5: numpy.array(
        [
            [0, 0, 0, 1, 1, 1, 1, 1, 1],
            [0, 0, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 0, 0, 0, 0, 0],
            [0, 1, 1, 0, 0, 0, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 0, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 0, 0, 1, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 1, 1, 1, 1],
            [0, 0, 0, 0, 0, 0, 1, 1, 1],
            [0, 0, 0, 0, 0, 0, 1, 1, 1],
            [1, 1, 1, 0, 0, 0, 1, 1, 0],
            [1, 1, 1, 1, 1, 1, 1, 0, 0],
        ]
    ),
    6: numpy.array(
        [
            [0, 0, 0, 1, 1, 1, 1],
            [0, 0, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 0, 0, 0],
            [0, 1, 1, 1, 0, 0, 0],
            [1, 1, 1, 0, 0, 0, 0],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1],
            [1, 1, 0, 0, 0, 1, 1],
            [1, 1, 0, 0, 0, 1, 1],
            [1, 1, 0, 0, 0, 1, 1],
            [1, 1, 1, 0, 0, 1, 1],
            [0, 1, 1, 1, 1, 1, 0],
        ]
    ),
    7: numpy.array(
        [
            [0, 0, 1, 1, 1, 1, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 0, 0, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0, 0, 1, 1, 0],
            [0, 0, 0, 0, 0, 1, 1, 0, 0],
            [0, 0, 0, 0, 0, 1, 1, 0, 0],
            [0, 0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0, 0],
            [0, 0, 0, 1, 1, 0, 0, 0, 0],
            [0, 0, 1, 1, 0, 0, 0, 0, 0],
        ]
    ),
    8: numpy.array(
        [
            [0, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 0, 0, 1, 1],
            [1, 1, 1, 0, 0, 0, 1, 1],
            [1, 1, 1, 1, 0, 0, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [0, 1, 1, 1, 1, 1, 1, 1],
        ]
    ),
    9: numpy.array(
        [
            [0, 1, 1, 1, 1, 1, 1, 0],
            [1, 1, 1, 0, 1, 1, 1, 0],
            [1, 1, 0, 0, 0, 1, 1, 0],
            [1, 1, 0, 0, 0, 1, 1, 1],
            [1, 1, 1, 0, 0, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 0],
            [0, 1, 1, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 0, 1, 1, 0],
            [0, 0, 0, 0, 1, 1, 1, 0],
            [0, 0, 0, 1, 1, 1, 1, 0],
            [0, 0, 1, 1, 1, 1, 0, 0],
            [1, 1, 1, 1, 1, 0, 0, 0],
            [1, 1, 0, 0, 0, 0, 0, 0],
        ]
    ),
}


class PlayInterface:
    """The interface toward DROD when playing the game."""

    def __init__(self):
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

    async def _click(self, position, right_click=False):
        pyautogui.click(
            x=self._origin_x + position[0],
            y=self._origin_y + position[1],
            button=pyautogui.SECONDARY if right_click else pyautogui.PRIMARY,
        )

    async def _click_tile(self, position, right_click=False):
        x, y = position
        await self._click(
            (
                ROOM_ORIGIN_X + (x + 0.5) * TILE_SIZE,
                ROOM_ORIGIN_Y + (y + 0.5) * TILE_SIZE,
            ),
            right_click=right_click,
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

    async def get_room_image(self, return_debug_images=False):
        """Get the room and minimap images from the DROD window.

        Parameters
        ----------
        return_debug_images
            If True, return an additional list of tuples (name, debug_image).

        Returns
        -------
        room_image
            The room.
        minimap
            The minimap.
        debug_images
            Only returned if `return_debug_images` is True. A list of (name, image).
        """
        if return_debug_images:
            debug_images = []

        if return_debug_images:
            _, _, image, window_debug_images = await get_drod_window(
                return_debug_images=True
            )
            debug_images.extend(window_debug_images)
            debug_images.append(("Extract DROD window", image))
        else:
            _, _, image = await get_drod_window()

        room_image = extract_room(image)
        if return_debug_images:
            debug_images.append(("Extract room", room_image))

        minimap = extract_minimap(image)
        if return_debug_images:
            debug_images.append(("Extract minimap", minimap))

        if return_debug_images:
            return room_image, minimap, debug_images
        return room_image, minimap

    async def get_orb_effects(
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

    async def get_right_click_info(self, monster_positions, return_debug_images=False):
        """Get right-click info for the given positions.

        Parameters
        ----------
        monster_positions
            The positions to get movement orders for.
        return_debug_images
            Whether to return debug images.

        Returns
        -------
        A dict mapping positions to movement orders. As a bonus, also return a dict
        mapping positions to the number of non-empty layers. If `return_debug_images`
        if True, also return a list of (name, image).
        """
        movement_orders = {}
        layer_counts = {}
        if return_debug_images:
            debug_images = []
        for position in monster_positions:
            await self._click_tile(position, right_click=True)
            _, _, image = await get_drod_window()
            room_image = extract_room(image)
            if return_debug_images:
                debug_images.append((f"Order screenshot {position}", room_image))
            white_pixels = find_color(room_image, (255, 255, 255))
            if return_debug_images:
                debug_images.append((f"White pixels {position}", white_pixels))
            labels, num_labels = scipy.ndimage.label(white_pixels)
            object_sizes = scipy.ndimage.sum_labels(
                white_pixels, labels, range(1, num_labels + 1)
            )
            largest_label = numpy.argmax(object_sizes) + 1
            largest_object = labels == largest_label
            if return_debug_images:
                debug_images.append((f"Largest white area {position}", largest_object))
            text_image = _extract_object(room_image, largest_object)
            if return_debug_images:
                debug_images.append((f"Text box {position}", text_image))
            layer_counts[position] = round((text_image.shape[0] - 4) / 21) - 1
            non_white = numpy.logical_not(find_color(text_image, (255, 255, 255)))
            if return_debug_images:
                debug_images.append((f"Non-white {position}", non_white))
            hash_eroded_image = scipy.ndimage.binary_erosion(non_white, _HASH_PATTERN)
            if return_debug_images:
                debug_images.append((f"Find hash {position}", hash_eroded_image))
            hash_location = numpy.argwhere(hash_eroded_image)
            if hash_location.shape[0] == 0:
                print(f"No hash character found at {position}")
                continue
            x = hash_location[0][1]
            y = hash_location[0][0]
            order_region = non_white[y - 8 : y + 10, x:]
            if return_debug_images:
                debug_images.append((f"Order region {position}", order_region))

            # Tuples of (x-coordinate, number)
            found_numbers = []
            for number, pattern in _NUMBER_PATTERNS.items():
                eroded_image = scipy.ndimage.binary_erosion(order_region, pattern)
                for coords in numpy.argwhere(eroded_image):
                    found_numbers.append((coords[1], number))
            found_numbers.sort(key=lambda t: t[0])
            order_number = int("".join([str(t[1]) for t in found_numbers]))
            if return_debug_images:
                debug_images.append(
                    (f"Number {position}", _make_text_image(str(order_number)))
                )
            # Movement order is displayed 1-indexed, but we use 0-indexed elsewhere
            movement_orders[position] = order_number - 1

        if return_debug_images:
            return movement_orders, layer_counts, debug_images
        return movement_orders, layer_counts


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


def _extract_object(image, object_mask):
    rows = numpy.any(object_mask, axis=1)
    columns = numpy.any(object_mask, axis=0)
    ymin, ymax = numpy.where(rows)[0][[0, -1]]
    xmin, xmax = numpy.where(columns)[0][[0, -1]]
    return image[ymin : ymax + 1, xmin : xmax + 1]


def _make_text_image(text):
    image = Image.new("1", (300, 200))
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("Pillow/Tests/fonts/FreeMono.ttf", 40)
    draw.text((10, 10), text, 1, font=font)
    return numpy.array(image)

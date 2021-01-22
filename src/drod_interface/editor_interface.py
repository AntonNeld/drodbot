import asyncio
from enum import Enum

import pyautogui

from common import (
    ROOM_WIDTH_IN_TILES,
    ROOM_HEIGHT_IN_TILES,
    TILE_SIZE,
)
from room import ElementType, Direction
from .consts import ROOM_ORIGIN_X, ROOM_ORIGIN_Y
from .util import get_drod_window, extract_room, extract_minimap, extract_tiles

_STYLE_SELECT_SCROLL_UP = (1000, 110)
_EDIT_ROOM = (670, 740)

_ROOM_PIECES_TAB = (24, 20)
_FLOOR_CONTROLS_TAB = (60, 20)
_ITEMS_TAB = (100, 20)
_MONSTERS_TAB = (135, 20)

_WALL = (30, 60)
_PIT = (60, 200)
_STAIRS = (135, 60)
_YELLOW_DOOR = (25, 170)
_YELLOW_DOOR_OPEN = (60, 170)
_GREEN_DOOR = (60, 105)
_GREEN_DOOR_OPEN = (60, 140)
_BLUE_DOOR = (25, 105)
_BLUE_DOOR_OPEN = (25, 140)
_MASTER_WALL = (90, 170)
_FLOOR = (25, 300)
_MOSAIC_FLOOR = (60, 300)
_ROAD_FLOOR = (90, 300)
_GRASS_FLOOR = (25, 330)
_DIRT_FLOOR = (60, 330)
_ALTERNATE_FLOOR = (90, 330)
_IMAGE_FLOOR = (120, 360)

_FORCE_ARROW = (30, 50)
_CHECKPOINT = (120, 50)
_WALL_LIGHT = (25, 85)

_ORB = (25, 50)
_MIMIC_POTION = (60, 50)
_SCROLL = (25, 115)
_OBSTACLE = (125, 115)
_OBSTACLE_STYLES = {
    "rock_1": (170, 80),
    "rock_2": (200, 80),
    "square_statue": (170, 115),
}
_TOKEN = (30, 180)
_CONQUER_TOKEN_IN_MENU = (265, 150)

_ROACH = (30, 50)
_CHARACTER = (110, 365)

_CHARACTER_WINDOW_SCROLL_UP = (960, 180)
_CHARACTER_WINDOW_FIRST_TYPE = (820, 180)
_CHARACTER_WINDOW_VISIBLE_CHECKBOX = (820, 700)
_CHARACTER_WINDOW_OKAY = (570, 710)

_IMAGE_SELECT_WINDOW_OKAY = (550, 670)

_IMAGE_IMPORT_WINDOW_FILE_NAME_INPUT = (400, 610)
_IMAGE_IMPORT_WINDOW_PNG = (300, 690)
_IMAGE_IMPORT_WINDOW_OKAY = (700, 680)

_STAIRS_WINDOW_OK = (545, 670)

_SCROLL_WINDOW_OK = (460, 580)


class _OrbType(Enum):
    NORMAL = 0
    CRACKED = 1
    BROKEN = 2


class EditorInterface:
    """The interface toward DROD when editing levels."""

    def __init__(self):
        # Will be set by initialize()
        self._origin_x = None
        self._origin_y = None
        self._selected_tab = None
        self._selected_element = {
            _ROOM_PIECES_TAB: None,
            _FLOOR_CONTROLS_TAB: None,
            _ITEMS_TAB: None,
            _MONSTERS_TAB: None,
        }
        self._hard_walls = None
        self._stairs_up = None
        self._hold_complete_wall = None
        self._force_arrow_direction = None
        self._orb_type = None
        self._monster_direction = None
        self._selected_token = None
        self._selected_obstacle = None
        self._copied_element = None
        self._copied_element_direction = None

    async def initialize(self):
        """Find the DROD window, focus it, and set the editor to a known state.

        This should be done before each user-triggered action, as the
        window will have lost focus and the user may have changed something.
        """
        origin_x, origin_y, _ = await get_drod_window()
        self._origin_x = origin_x
        self._origin_y = origin_y
        await self._click((3, 3))
        # Let's use raw clicks here instead of select_element().
        # The latter depend on the state being set up.
        await self._click(_ROOM_PIECES_TAB)
        # Check whether we have selected master wall or hold complete wall
        await self._click(_MASTER_WALL)
        _, _, image = await get_drod_window()
        # Look for part of the "Hold complete wall" text
        self._hold_complete_wall = image[455, 145, 0] == 0
        # Check stairs direction
        await self._click(_STAIRS)
        _, _, image = await get_drod_window()
        # Look for part of the "up" text
        self._stairs_up = image[455, 57, 0] == 9
        # Check whether the wall is normal or hard
        await self._click(_WALL)
        _, _, image = await get_drod_window()
        # Look for part of the "(hard)" text
        self._hard_walls = image[457, 62, 0] == 22
        self._selected_element[_ROOM_PIECES_TAB] = _WALL

        await self._click(_FLOOR_CONTROLS_TAB)
        await self._click(_FORCE_ARROW)
        self._selected_element[_FLOOR_CONTROLS_TAB] = _FORCE_ARROW
        # Make sure the force arrows are facing SE
        _, _, image = await get_drod_window()
        while image[60, 35, 0] != 165:  # The tip of the arrow when facing SE
            pyautogui.press("q")
            _, _, image = await get_drod_window()
        self._force_arrow_direction = Direction.SE

        await self._click(_ITEMS_TAB)
        await self._click(_ORB)
        self._selected_element[_ITEMS_TAB] = _ORB
        _, _, image = await get_drod_window()
        while image[455, 45, 0] != 255:  # Background instead of open parenthesis
            pyautogui.press("q")
            _, _, image = await get_drod_window()
        self._orb_type = _OrbType.NORMAL

        await self._click(_MONSTERS_TAB)
        self._selected_tab = _MONSTERS_TAB
        await self._click(_ROACH)
        self._selected_element[_MONSTERS_TAB] = _ROACH
        # Make sure the monsters are facing SE
        _, _, image = await get_drod_window()
        while image[26, 140, 0] != 240:  # The roach's eye when facing SE
            pyautogui.press("q")
            _, _, image = await get_drod_window()
        self._monster_direction = Direction.SE

    async def _click(self, position, button="left"):
        pyautogui.click(
            x=self._origin_x + position[0],
            y=self._origin_y + position[1],
            button=button,
        )

    async def _select_element(self, tab_position, element_position):
        if self._selected_tab != tab_position:
            await self._click(tab_position)
            self._selected_tab = tab_position
        if self._selected_element[tab_position] != element_position:
            await self._click(element_position)
            self._selected_element[tab_position] = element_position

    async def clear_room(self):
        """Clear the entire room, leaving only normal floors.

        This includes removing the side walls.
        """
        # Select the normal floor, to make sure clearing doesn't use special floors
        await self._select_element(_ROOM_PIECES_TAB, _FLOOR)
        pyautogui.keyDown("shift")
        pyautogui.moveTo(
            x=self._origin_x + ROOM_ORIGIN_X + TILE_SIZE * 0.5,
            y=self._origin_y + ROOM_ORIGIN_Y + TILE_SIZE * 0.5,
        )
        pyautogui.dragRel(
            xOffset=(ROOM_WIDTH_IN_TILES - 1) * TILE_SIZE,
            yOffset=(ROOM_HEIGHT_IN_TILES - 1) * TILE_SIZE,
            button="right",
        )
        pyautogui.keyUp("shift")

    async def clear_tile(self, position):
        """Clear the given tile.

        Parameters
        ----------
        position
            Position of the tile.
        """
        # Select the normal floor, to make sure clearing doesn't use special floors
        await self._select_element(_ROOM_PIECES_TAB, _FLOOR)
        pyautogui.keyDown("shift")
        pyautogui.click(
            x=self._origin_x + ROOM_ORIGIN_X + TILE_SIZE * (position[0] + 0.5),
            y=self._origin_y + ROOM_ORIGIN_Y + TILE_SIZE * (position[1] + 0.5),
            button="right",
        )
        pyautogui.keyUp("shift")

    async def _set_direction(self, direction, kind="monster"):
        # Warning: Does not make sure that the correct element is selected
        if kind == "monster":
            attribute = "_monster_direction"
        elif kind == "force_arrow":
            attribute = "_force_arrow_direction"
        direction_to_number = {
            Direction.N: 0,
            Direction.NE: 1,
            Direction.E: 2,
            Direction.SE: 3,
            Direction.S: 4,
            Direction.SW: 5,
            Direction.W: 6,
            Direction.NW: 7,
        }
        clockwise_rotations = (
            direction_to_number[direction]
            - direction_to_number[getattr(self, attribute)]
        ) % 8
        if clockwise_rotations <= 4:
            for _ in range(clockwise_rotations):
                pyautogui.press("w")
        else:  # Quicker to go counterclockwise
            for _ in range(8 - clockwise_rotations):
                pyautogui.press("q")
        setattr(self, attribute, direction)

    async def set_floor_image(self, directory, base_name):
        """Set the image to use for image floors.

        Only supports PNG images, and assumes that there are no other
        images imported.

        Parameters
        ----------
        directory
            Path to the directory containing the image.
        base_name
            The file name of the image, without the extension.
        """
        await self._select_element(_ROOM_PIECES_TAB, _IMAGE_FLOOR)
        pyautogui.press("f9")
        _, _, image = await get_drod_window()
        imported_image = image[198, 199, 0] == 190
        await self._click(_IMAGE_SELECT_WINDOW_OKAY)
        if not imported_image:
            # Replace the directory input
            pyautogui.keyDown("ctrl")
            pyautogui.press("a")
            pyautogui.keyUp("ctrl")
            pyautogui.press("backspace")
            pyautogui.write(directory)
            pyautogui.press("enter")
            # Replace the file name input
            await self._click(_IMAGE_IMPORT_WINDOW_FILE_NAME_INPUT)
            pyautogui.keyDown("ctrl")
            pyautogui.press("a")
            pyautogui.keyUp("ctrl")
            pyautogui.press("backspace")
            pyautogui.write(base_name)
            # Select PNG and confirm
            await self._click(_IMAGE_IMPORT_WINDOW_PNG)
            await asyncio.sleep(0.1)
            await self._click(_IMAGE_IMPORT_WINDOW_OKAY)
            await self._click(_IMAGE_SELECT_WINDOW_OKAY)
        # Need to click somewhere to get back to normal mode
        await self._click((ROOM_ORIGIN_X + 10, ROOM_ORIGIN_Y + 10))

    async def place_element(
        self,
        element,
        direction,
        position,
        end_position=None,
        copy_characters=False,
        style=None,
    ):
        """Place an element in the editor.

        Parameters
        ----------
        element
            The element to place.
        position
            The tile to place it in, as a tuple (x, y). If `end_position`
            is not None, this is the upper left corner.
        end_position
            If this is set, place the element in a rectangle with this as
            its lower right corner and `position` as its upper right corner.
            Not all elements can be placed like this.
        copy_characters
            If this is set, copy characters after placing them and paste instead
            of creating a new one if placing the same character (in the same direction)
            again. This has the side effect of copying the entire contents of the tile,
            so this should only be done if we know the tile is otherwise empty, e.g. by
            placing all characters before any other layers.
        style
            The cosmetic style of the element. It does not count as a separate element
            in the model (the ElementType enum), but may be of interest to place anyway.
            The possible values depend on the element to place.
        """
        button = "left"
        if element in [ElementType.BEETHRO]:
            # Some elements cannot be placed freely, so we place characters to fake it
            await self._place_character(
                element, direction, position, copy_characters=copy_characters
            )
            return

        if element == ElementType.WALL:
            await self._select_element(_ROOM_PIECES_TAB, _WALL)
            if (style == "hard") != self._hard_walls:
                await self._click(_WALL)
                self._hard_walls = style == "hard"
        elif element == ElementType.PIT:
            await self._select_element(_ROOM_PIECES_TAB, _PIT)
        elif element == ElementType.STAIRS:
            await self._select_element(_ROOM_PIECES_TAB, _STAIRS)
            if (style == "up") != self._stairs_up:
                await self._click(_STAIRS)
                self._stairs_up = style == "up"
        elif element == ElementType.FLOOR:
            button = "right"
            if style == "mosaic":
                await self._select_element(_ROOM_PIECES_TAB, _MOSAIC_FLOOR)
            elif style == "road":
                await self._select_element(_ROOM_PIECES_TAB, _ROAD_FLOOR)
            elif style == "grass":
                await self._select_element(_ROOM_PIECES_TAB, _GRASS_FLOOR)
            elif style == "dirt":
                await self._select_element(_ROOM_PIECES_TAB, _DIRT_FLOOR)
            elif style == "alternate":
                await self._select_element(_ROOM_PIECES_TAB, _ALTERNATE_FLOOR)
            elif style == "image":
                await self._select_element(_ROOM_PIECES_TAB, _IMAGE_FLOOR)
                # This floor doesn't behave like the others, and should be
                # created with the left button
                button = "left"
            else:
                await self._select_element(_ROOM_PIECES_TAB, _FLOOR)
        elif element == ElementType.YELLOW_DOOR:
            await self._select_element(_ROOM_PIECES_TAB, _YELLOW_DOOR)
        elif element == ElementType.YELLOW_DOOR_OPEN:
            await self._select_element(_ROOM_PIECES_TAB, _YELLOW_DOOR_OPEN)
        elif element == ElementType.GREEN_DOOR:
            await self._select_element(_ROOM_PIECES_TAB, _GREEN_DOOR)
        elif element == ElementType.GREEN_DOOR_OPEN:
            await self._select_element(_ROOM_PIECES_TAB, _GREEN_DOOR_OPEN)
        elif element == ElementType.BLUE_DOOR:
            await self._select_element(_ROOM_PIECES_TAB, _BLUE_DOOR)
        elif element == ElementType.BLUE_DOOR_OPEN:
            await self._select_element(_ROOM_PIECES_TAB, _BLUE_DOOR_OPEN)
        elif element == ElementType.MASTER_WALL:
            await self._select_element(_ROOM_PIECES_TAB, _MASTER_WALL)
            if self._hold_complete_wall:
                await self._click(_MASTER_WALL)
                self._hold_complete_wall = False
        elif element == ElementType.FORCE_ARROW:
            await self._select_element(_FLOOR_CONTROLS_TAB, _FORCE_ARROW)
            await self._set_direction(direction, kind="force_arrow")
        elif element == ElementType.CHECKPOINT:
            await self._select_element(_FLOOR_CONTROLS_TAB, _CHECKPOINT)
        elif element == ElementType.ORB:
            await self._select_element(_ITEMS_TAB, _ORB)
            if self._orb_type == _OrbType.CRACKED:
                await self._click(_ORB)
                await self._click(_ORB)
            elif self._orb_type == _OrbType.BROKEN:
                await self._click(_ORB)
            self._orb_type = _OrbType.NORMAL
        elif element == ElementType.SCROLL:
            await self._select_element(_ITEMS_TAB, _SCROLL)
        elif element == ElementType.OBSTACLE:
            used_style = style if style is not None else "rock_1"
            await self._select_element(_ITEMS_TAB, _OBSTACLE)
            if self._selected_obstacle != _OBSTACLE_STYLES[used_style]:
                # Click it again to bring up the menu, and select the right style
                await self._click(_OBSTACLE)
                await self._click(_OBSTACLE_STYLES[used_style])
                self._selected_obstacle = _OBSTACLE_STYLES[used_style]
        elif element == ElementType.CONQUER_TOKEN:
            await self._select_element(_ITEMS_TAB, _TOKEN)
            if self._selected_token != _CONQUER_TOKEN_IN_MENU:
                # Click it again to bring up the menu, and select it
                await self._click(_TOKEN)
                await self._click(_CONQUER_TOKEN_IN_MENU)
                self._selected_token = _CONQUER_TOKEN_IN_MENU
        elif element == ElementType.ROACH:
            await self._select_element(_MONSTERS_TAB, _ROACH)
            await self._set_direction(direction)
        else:
            raise RuntimeError(f"Unknown element {element}")
        if end_position is None:
            await self._click(
                (
                    ROOM_ORIGIN_X + (position[0] + 0.5) * TILE_SIZE,
                    ROOM_ORIGIN_Y + (position[1] + 0.5) * TILE_SIZE,
                ),
                button=button,
            )
        else:
            pyautogui.moveTo(
                x=self._origin_x + ROOM_ORIGIN_X + TILE_SIZE * (position[0] + 0.5),
                y=self._origin_y + ROOM_ORIGIN_Y + TILE_SIZE * (position[1] + 0.5),
            )
            pyautogui.dragRel(
                xOffset=(end_position[0] - position[0]) * TILE_SIZE,
                yOffset=(end_position[1] - position[1]) * TILE_SIZE,
                button=button,
            )
        if element == ElementType.STAIRS:
            # Close the stairs window, it doesn't matter where the stairs go
            await self._click(_STAIRS_WINDOW_OK)
        elif element == ElementType.SCROLL:
            # Write something and close the scroll window
            pyautogui.press("space")
            await self._click(_SCROLL_WINDOW_OK)

    async def _place_character(
        self, element, direction, position, copy_characters=False
    ):
        real_x = ROOM_ORIGIN_X + (position[0] + 0.5) * TILE_SIZE
        real_y = ROOM_ORIGIN_Y + (position[1] + 0.5) * TILE_SIZE
        if (
            copy_characters
            and self._copied_element == element
            and self._copied_element_direction == direction
        ):
            # Paste the character
            pyautogui.keyDown("ctrl")
            pyautogui.press("v")
            pyautogui.keyUp("ctrl")
            await self._click((real_x, real_y))
        else:
            await self._select_element(_MONSTERS_TAB, _CHARACTER)
            await self._set_direction(direction)
            await self._click((real_x, real_y))
            # We're now in the character menu
            if element == ElementType.BEETHRO:
                await self._click(_CHARACTER_WINDOW_SCROLL_UP)
                await self._click(_CHARACTER_WINDOW_SCROLL_UP)
                await self._click(_CHARACTER_WINDOW_FIRST_TYPE)
            await self._click(_CHARACTER_WINDOW_VISIBLE_CHECKBOX)
            await self._click(_CHARACTER_WINDOW_OKAY)
            if copy_characters:
                # Copy the character
                pyautogui.mouseDown(
                    x=self._origin_x + real_x, y=self._origin_y + real_y
                )
                pyautogui.keyDown("ctrl")
                pyautogui.press("c")
                pyautogui.keyUp("ctrl")
                pyautogui.mouseUp()
                pyautogui.press("esc")  # Leave pasting mode
                self._copied_element = element
                self._copied_element_direction = direction

    async def start_test_room(self, position, direction):
        """Start testing the room.

        Parameters
        ----------
        position
            The position to start in as a tuple (x, y).
        direction
            The direction to face when starting.
        """
        # Select the roach to make sure we can rotate monsters
        await self._select_element(_MONSTERS_TAB, _ROACH)
        await self._set_direction(direction)
        pyautogui.press("f5")
        await self._click(
            (
                ROOM_ORIGIN_X + (position[0] + 0.5) * TILE_SIZE,
                ROOM_ORIGIN_Y + (position[1] + 0.5) * TILE_SIZE,
            )
        )
        # Move the mouse out of the way
        pyautogui.moveTo(self._origin_x + 3, self._origin_y + 3)
        # Sleep to let the transition finish
        await asyncio.sleep(3)

    async def stop_test_room(self):
        """Stop testing the room."""
        pyautogui.press("esc")
        # Sleep to let the transition finish
        await asyncio.sleep(1)

    async def select_first_style(self):
        """Select the first room style for the current room."""
        pyautogui.press("esc")
        await self._click(_STYLE_SELECT_SCROLL_UP)
        pyautogui.press("up", presses=13, interval=0.1)
        await self._click(_EDIT_ROOM)

    async def select_next_style(self):
        """Select the next room style for the current room."""
        pyautogui.press("esc")
        await self._click(_STYLE_SELECT_SCROLL_UP)
        pyautogui.press("down")
        await self._click(_EDIT_ROOM)

    async def get_tiles_and_colors(self):
        """Get the tiles and minimap colors for each coordinate.

        Returns
        -------
        tiles
            A dict with coordinates as keys and tile images as values.
        colors
            A dict with coordinates as keys and (r, g, b) tuples as values.
        """
        _, _, window_image = await get_drod_window()
        room_image = extract_room(window_image)
        minimap_image = extract_minimap(window_image)
        return extract_tiles(room_image, minimap_image)

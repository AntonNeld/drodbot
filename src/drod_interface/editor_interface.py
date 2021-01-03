import asyncio

import pyautogui

from common import (
    ROOM_WIDTH_IN_TILES,
    ROOM_HEIGHT_IN_TILES,
    TILE_SIZE,
    Element,
    Direction,
)
from .consts import ROOM_ORIGIN_X, ROOM_ORIGIN_Y
from .util import get_drod_window, extract_room, extract_minimap, extract_tiles

STYLE_SELECT_SCROLL_UP = (1000, 110)
EDIT_ROOM = (670, 740)

ROOM_PIECES_TAB = (24, 20)
FLOOR_CONTROLS_TAB = (60, 20)
ITEMS_TAB = (100, 20)
MONSTERS_TAB = (135, 20)

WALL = (30, 60)
FLOOR = (25, 300)

FORCE_ARROW = (30, 50)
CHECKPOINT = (120, 50)
WALL_LIGHT = (25, 85)

MIMIC = (60, 50)
TOKEN = (30, 180)
CONQUER_TOKEN_IN_MENU = (265, 150)

ROACH = (30, 50)
CHARACTER = (110, 365)

CHARACTER_WINDOW_SCROLL_UP = (960, 180)
CHARACTER_WINDOW_FIRST_TYPE = (820, 180)
CHARACTER_WINDOW_VISIBLE_CHECKBOX = (820, 700)
CHARACTER_WINDOW_OKAY = (570, 710)


class EditorInterface:
    def __init__(self):
        # Will be set by initialize()
        self.origin_x = None
        self.origin_y = None
        self.selected_tab = None
        self.selected_element = {
            ROOM_PIECES_TAB: None,
            FLOOR_CONTROLS_TAB: None,
            ITEMS_TAB: None,
            MONSTERS_TAB: None,
        }
        self.hard_walls = None
        self.monster_direction = None
        self.selected_token = None
        self.copied_element = None
        self.copied_element_direction = None

    async def initialize(self):
        """Find the DROD window and focus it.

        This should be done before each user-triggered action, as the
        window will have lost focus.
        """
        origin_x, origin_y, _ = await get_drod_window()
        self.origin_x = origin_x
        self.origin_y = origin_y
        await self._click((3, 3))
        # Let's use raw clicks here instead of select_element().
        # The latter depend on the state being set up.
        await self._click(ROOM_PIECES_TAB)
        # Check whether the wall is normal or hard
        await self._click(WALL)
        self.selected_element[ROOM_PIECES_TAB] = WALL
        _, _, image = await get_drod_window()
        # Check for part of the "(hard)" text
        self.hard_walls = image[457, 62, 0] == 22

        # For now, only select the force arrow. Once we start using it, we need to
        # check its direction as well.
        await self._click(FLOOR_CONTROLS_TAB)
        await self._click(FORCE_ARROW)
        self.selected_element[FLOOR_CONTROLS_TAB] = FORCE_ARROW

        await self._click(ITEMS_TAB)
        await self._click(MIMIC)
        self.selected_element[ITEMS_TAB] = MIMIC

        await self._click(MONSTERS_TAB)
        self.selected_tab = MONSTERS_TAB
        await self._click(ROACH)
        self.selected_element[MONSTERS_TAB] = ROACH
        # Make sure the monsters are facing SE
        _, _, image = await get_drod_window()
        while image[26, 140, 0] != 240:  # The roach's eye when facing SE
            pyautogui.press("q")
            _, _, image = await get_drod_window()
        self.monster_direction = Direction.SE

    async def _click(self, position, button="left"):
        pyautogui.click(
            x=self.origin_x + position[0], y=self.origin_y + position[1], button=button
        )

    async def _select_element(self, tab_position, element_position):
        if self.selected_tab != tab_position:
            await self._click(tab_position)
            self.selected_tab = tab_position
        if self.selected_element[tab_position] != element_position:
            await self._click(element_position)
            self.selected_element[tab_position] = element_position

    async def clear_room(self):
        # Select the normal floor, to make sure clearing doesn't use mosaic floors
        await self._select_element(ROOM_PIECES_TAB, FLOOR)
        pyautogui.keyDown("shift")
        pyautogui.moveTo(
            x=self.origin_x + ROOM_ORIGIN_X + TILE_SIZE * 0.5,
            y=self.origin_y + ROOM_ORIGIN_Y + TILE_SIZE * 0.5,
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
        # Select the normal floor, to make sure clearing doesn't use mosaic floors
        await self._select_element(ROOM_PIECES_TAB, FLOOR)
        pyautogui.keyDown("shift")
        pyautogui.click(
            x=self.origin_x + ROOM_ORIGIN_X + TILE_SIZE * (position[0] + 0.5),
            y=self.origin_y + ROOM_ORIGIN_Y + TILE_SIZE * (position[1] + 0.5),
            button="right",
        )
        pyautogui.keyUp("shift")

    async def _set_monster_direction(self, direction):
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
            direction_to_number[direction] - direction_to_number[self.monster_direction]
        ) % 8
        if clockwise_rotations <= 4:
            for _ in range(clockwise_rotations):
                pyautogui.press("w")
        else:  # Quicker to go counterclockwise
            for _ in range(8 - clockwise_rotations):
                pyautogui.press("q")
        self.monster_direction = direction

    async def place_element(
        self,
        element,
        direction,
        position,
        end_position=None,
        copy_characters=False,
        hard_wall=False,
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
        hard_wall
            Only used when placing walls. If this is true, the wall will be
            of the hard variant.
        """
        button = "left"
        if element in [Element.BEETHRO]:
            # Some elements cannot be placed freely, so we place characters to fake it
            if end_position is not None:
                raise RuntimeError("Cannot place character in a rectangle")
            await self._place_character(
                element, direction, position, copy_characters=copy_characters
            )
            return

        if element == Element.WALL:
            await self._select_element(ROOM_PIECES_TAB, WALL)
            if hard_wall != self.hard_walls:
                await self._click(WALL)
                self.hard_walls = hard_wall
        elif element == Element.FLOOR:
            await self._select_element(ROOM_PIECES_TAB, FLOOR)
            button = "right"
        elif element == Element.CONQUER_TOKEN:
            await self._select_element(ITEMS_TAB, TOKEN)
            if self.selected_token != CONQUER_TOKEN_IN_MENU:
                # Click it again to bring up the menu, and select it
                await self._click(TOKEN)
                await self._click(CONQUER_TOKEN_IN_MENU)
                self.selected_token = CONQUER_TOKEN_IN_MENU
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
                x=self.origin_x + ROOM_ORIGIN_X + TILE_SIZE * (position[0] + 0.5),
                y=self.origin_y + ROOM_ORIGIN_Y + TILE_SIZE * (position[1] + 0.5),
            )
            pyautogui.dragRel(
                xOffset=(end_position[0] - position[0]) * TILE_SIZE,
                yOffset=(end_position[1] - position[1]) * TILE_SIZE,
                button=button,
            )

    async def _place_character(
        self, element, direction, position, copy_characters=False
    ):
        real_x = ROOM_ORIGIN_X + (position[0] + 0.5) * TILE_SIZE
        real_y = ROOM_ORIGIN_Y + (position[1] + 0.5) * TILE_SIZE
        if (
            copy_characters
            and self.copied_element == element
            and self.copied_element_direction == direction
        ):
            # Paste the character
            pyautogui.keyDown("ctrl")
            pyautogui.press("v")
            pyautogui.keyUp("ctrl")
            await self._click((real_x, real_y))
        else:
            await self._select_element(MONSTERS_TAB, CHARACTER)
            await self._set_monster_direction(direction)
            await self._click((real_x, real_y))
            # We're now in the character menu
            if element == Element.BEETHRO:
                await self._click(CHARACTER_WINDOW_SCROLL_UP)
                await self._click(CHARACTER_WINDOW_SCROLL_UP)
                await self._click(CHARACTER_WINDOW_FIRST_TYPE)
            await self._click(CHARACTER_WINDOW_VISIBLE_CHECKBOX)
            await self._click(CHARACTER_WINDOW_OKAY)
            if copy_characters:
                # Copy the character
                pyautogui.mouseDown(x=self.origin_x + real_x, y=self.origin_y + real_y)
                pyautogui.keyDown("ctrl")
                pyautogui.press("c")
                pyautogui.keyUp("ctrl")
                pyautogui.press("esc")  # Leave pasting mode
                self.copied_element = element
                self.copied_element_direction = direction

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
        await self._select_element(MONSTERS_TAB, ROACH)
        await self._set_monster_direction(direction)
        pyautogui.press("f5")
        await self._click(
            (
                ROOM_ORIGIN_X + (position[0] + 0.5) * TILE_SIZE,
                ROOM_ORIGIN_Y + (position[1] + 0.5) * TILE_SIZE,
            )
        )
        # Move the mouse out of the way
        pyautogui.moveTo(self.origin_x + 3, self.origin_y + 3)
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
        await self._click(STYLE_SELECT_SCROLL_UP)
        pyautogui.press("up", presses=13, interval=0.1)
        await self._click(EDIT_ROOM)

    async def select_next_style(self):
        """Select the next room style for the current room."""
        pyautogui.press("esc")
        await self._click(STYLE_SELECT_SCROLL_UP)
        pyautogui.press("down")
        await self._click(EDIT_ROOM)

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

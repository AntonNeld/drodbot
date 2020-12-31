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
from .util import get_drod_window, extract_room, extract_tiles

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

    async def _click(self, position):
        pyautogui.click(x=self.origin_x + position[0], y=self.origin_y + position[1])

    async def _select_element(self, tab_position, element_position):
        if self.selected_tab != tab_position:
            await self._click(tab_position)
            self.selected_tab = tab_position
        if self.selected_element[tab_position] != element_position:
            await self._click(element_position)
            self.selected_element[tab_position] = element_position

    async def clear_room(self):
        # Select the normal floor, so clearing doesn't use mosaic floors
        await self._select_element(ROOM_PIECES_TAB, FLOOR)
        await self._clear_layer()

        # The floor controls tab contains three layers (disregarding level entrances),
        # which need to be cleared separately
        await self._select_element(FLOOR_CONTROLS_TAB, FORCE_ARROW)
        await self._clear_layer()
        await self._select_element(FLOOR_CONTROLS_TAB, CHECKPOINT)
        await self._clear_layer()
        await self._select_element(FLOOR_CONTROLS_TAB, WALL_LIGHT)
        await self._clear_layer()

        await self._select_element(ITEMS_TAB, MIMIC)
        await self._clear_layer()

        await self._select_element(MONSTERS_TAB, ROACH)
        await self._clear_layer()

    async def _clear_layer(self):
        pyautogui.moveTo(
            x=self.origin_x + ROOM_ORIGIN_X + TILE_SIZE * 0.5,
            y=self.origin_y + ROOM_ORIGIN_Y + TILE_SIZE * 0.5,
        )
        pyautogui.dragRel(
            xOffset=(ROOM_WIDTH_IN_TILES - 1) * TILE_SIZE,
            yOffset=(ROOM_HEIGHT_IN_TILES - 1) * TILE_SIZE,
            button="right",
        )

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
        self, element, direction, position, end_position=None, hard_wall=False
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
        hard_wall
            Only used when placing walls. If this is true, the wall will be
            of the hard variant.
        """
        if element == Element.WALL:
            await self._select_element(ROOM_PIECES_TAB, WALL)
            if hard_wall != self.hard_walls:
                await self._click(WALL)
                self.hard_walls = hard_wall
        elif element == Element.CONQUER_TOKEN:
            await self._select_element(ITEMS_TAB, TOKEN)
            # Click it again to bring up the menu, and select it
            await self._click(TOKEN)
            await self._click(CONQUER_TOKEN_IN_MENU)
        elif element == Element.BEETHRO:
            # We cannot place a Beethro, so we'll make a character that looks like him
            await self._select_element(MONSTERS_TAB, CHARACTER)
            await self._set_monster_direction(direction)
            if end_position is not None:
                raise RuntimeError("Cannot place character in a rectangle")
        else:
            raise RuntimeError(f"Unknown element {element}")
        if end_position is None:
            await self._click(
                (
                    ROOM_ORIGIN_X + (position[0] + 0.5) * TILE_SIZE,
                    ROOM_ORIGIN_Y + (position[1] + 0.5) * TILE_SIZE,
                )
            )
        else:
            pyautogui.moveTo(
                x=self.origin_x + ROOM_ORIGIN_X + TILE_SIZE * (position[0] + 0.5),
                y=self.origin_y + ROOM_ORIGIN_Y + TILE_SIZE * (position[1] + 0.5),
            )
            pyautogui.dragRel(
                xOffset=(end_position[0] - position[0]) * TILE_SIZE,
                yOffset=(end_position[1] - position[1]) * TILE_SIZE,
            )
        # Go into the character menu to make the character look like Beethro.
        if element == Element.BEETHRO:
            await self._click(CHARACTER_WINDOW_SCROLL_UP)
            await self._click(CHARACTER_WINDOW_SCROLL_UP)
            await self._click(CHARACTER_WINDOW_FIRST_TYPE)
            await self._click(CHARACTER_WINDOW_VISIBLE_CHECKBOX)
            await self._click(CHARACTER_WINDOW_OKAY)

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

    async def get_tiles(self):
        _, _, window_image = await get_drod_window()
        room_image = extract_room(window_image)
        return extract_tiles(room_image)

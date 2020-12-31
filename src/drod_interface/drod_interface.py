import asyncio

import numpy
import pyautogui

from common import (
    ROOM_WIDTH_IN_TILES,
    ROOM_HEIGHT_IN_TILES,
    Action,
    GUIEvent,
    ImageProcessingStep,
    Element,
    Direction,
    Room,
)
from .classify import classify_tile
from .util import get_drod_window

ROOM_ORIGIN_X = 163
ROOM_ORIGIN_Y = 40

TILE_SIZE = 22

EDITOR_ROOM_PIECES_TAB = (24, 20)
EDITOR_FLOOR_CONTROLS_TAB = (60, 20)
EDITOR_ITEMS_TAB = (100, 20)
EDITOR_MONSTERS_TAB = (135, 20)

EDITOR_WALL = (30, 60)
EDITOR_FLOOR = (25, 300)

EDITOR_FORCE_ARROW = (30, 50)
EDITOR_CHECKPOINT = (120, 50)
EDITOR_WALL_LIGHT = (25, 85)

EDITOR_MIMIC = (60, 50)
EDITOR_TOKEN = (30, 180)
EDITOR_CONQUER_TOKEN_IN_MENU = (265, 150)

EDITOR_ROACH = (30, 50)
EDITOR_CHARACTER = (110, 365)

EDITOR_CHARACTER_WINDOW_SCROLL_UP = (960, 180)
EDITOR_CHARACTER_WINDOW_FIRST_TYPE = (820, 180)
EDITOR_CHARACTER_WINDOW_VISIBLE_CHECKBOX = (820, 700)
EDITOR_CHARACTER_WINDOW_OKAY = (570, 710)


class DrodInterface:
    def __init__(self, window_queue):
        self._queue = window_queue
        # Will be set by initialize()
        self.origin_x = None
        self.origin_y = None
        # Editor state, will be set by initialize(editor=True)
        self.editor_selected_tab = None
        self.editor_selected_element = {
            EDITOR_ROOM_PIECES_TAB: None,
            EDITOR_FLOOR_CONTROLS_TAB: None,
            EDITOR_ITEMS_TAB: None,
            EDITOR_MONSTERS_TAB: None,
        }
        self.editor_hard_walls = None
        self.editor_monster_direction = None

    async def initialize(self, editor=False):
        """Find the DROD window and focus it.

        This should be done before each user-triggered action, as the
        window will have lost focus.

        Parameters
        ----------
        editor
            Whether we are in the editor. If this is true, ensure the internal
            state matches the editor's state.
        """
        origin_x, origin_y, _ = await get_drod_window()
        self.origin_x = origin_x
        self.origin_y = origin_y
        await self._click((3, 3))
        # Let's use raw clicks here instead of editor_select_element().
        # The latter depend on the state being set up.
        if editor:
            await self._click(EDITOR_ROOM_PIECES_TAB)
            # Check whether the wall is normal or hard
            await self._click(EDITOR_WALL)
            self.editor_selected_element[EDITOR_ROOM_PIECES_TAB] = EDITOR_WALL
            _, _, image = await get_drod_window()
            # Check for part of the "(hard)" text
            self.editor_hard_walls = image[457, 62, 0] == 22

            # For now, only select the force arrow. Once we start using it, we need to
            # check its direction as well.
            await self._click(EDITOR_FLOOR_CONTROLS_TAB)
            await self._click(EDITOR_FORCE_ARROW)
            self.editor_selected_element[EDITOR_FLOOR_CONTROLS_TAB] = EDITOR_FORCE_ARROW

            await self._click(EDITOR_ITEMS_TAB)
            await self._click(EDITOR_MIMIC)
            self.editor_selected_element[EDITOR_ITEMS_TAB] = EDITOR_MIMIC

            await self._click(EDITOR_MONSTERS_TAB)
            self.editor_selected_tab = EDITOR_MONSTERS_TAB
            await self._click(EDITOR_ROACH)
            self.editor_selected_element[EDITOR_MONSTERS_TAB] = EDITOR_ROACH
            # Make sure the monsters are facing SE
            _, _, image = await get_drod_window()
            while image[26, 140, 0] != 240:  # The roach's eye when facing SE
                pyautogui.press("q")
                _, _, image = await get_drod_window()
            self.editor_monster_direction = Direction.SE

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

    async def _click(self, position):
        pyautogui.click(x=self.origin_x + position[0], y=self.origin_y + position[1])

    async def _editor_select_element(self, tab_position, element_position):
        if self.editor_selected_tab != tab_position:
            await self._click(tab_position)
            self.editor_selected_tab = tab_position
        if self.editor_selected_element[tab_position] != element_position:
            await self._click(element_position)
            self.editor_selected_element[tab_position] = element_position

    async def editor_clear_room(self):
        # Select the normal floor, so clearing doesn't use mosaic floors
        await self._editor_select_element(EDITOR_ROOM_PIECES_TAB, EDITOR_FLOOR)
        await self._editor_clear_layer()

        # The floor controls tab contains three layers (disregarding level entrances),
        # which need to be cleared separately
        await self._editor_select_element(EDITOR_FLOOR_CONTROLS_TAB, EDITOR_FORCE_ARROW)
        await self._editor_clear_layer()
        await self._editor_select_element(EDITOR_FLOOR_CONTROLS_TAB, EDITOR_CHECKPOINT)
        await self._editor_clear_layer()
        await self._editor_select_element(EDITOR_FLOOR_CONTROLS_TAB, EDITOR_WALL_LIGHT)
        await self._editor_clear_layer()

        await self._editor_select_element(EDITOR_ITEMS_TAB, EDITOR_MIMIC)
        await self._editor_clear_layer()

        await self._editor_select_element(EDITOR_MONSTERS_TAB, EDITOR_ROACH)
        await self._editor_clear_layer()

    async def _editor_clear_layer(self):
        pyautogui.moveTo(
            x=self.origin_x + ROOM_ORIGIN_X + TILE_SIZE * 0.5,
            y=self.origin_y + ROOM_ORIGIN_Y + TILE_SIZE * 0.5,
        )
        pyautogui.dragRel(
            xOffset=(ROOM_WIDTH_IN_TILES - 1) * TILE_SIZE,
            yOffset=(ROOM_HEIGHT_IN_TILES - 1) * TILE_SIZE,
            button="right",
        )

    async def _editor_set_monster_direction(self, direction):
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
            - direction_to_number[self.editor_monster_direction]
        ) % 8
        if clockwise_rotations <= 4:
            for _ in range(clockwise_rotations):
                pyautogui.press("w")
        else:  # Quicker to go counterclockwise
            for _ in range(8 - clockwise_rotations):
                pyautogui.press("q")
        self.editor_monster_direction = direction

    async def editor_place_element(
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
            await self._editor_select_element(EDITOR_ROOM_PIECES_TAB, EDITOR_WALL)
            if hard_wall != self.editor_hard_walls:
                await self._click(EDITOR_WALL)
                self.editor_hard_walls = hard_wall
        elif element == Element.CONQUER_TOKEN:
            await self._editor_select_element(EDITOR_ITEMS_TAB, EDITOR_TOKEN)
            # Click it again to bring up the menu, and select it
            await self._click(EDITOR_TOKEN)
            await self._click(EDITOR_CONQUER_TOKEN_IN_MENU)
        elif element == Element.BEETHRO:
            # We cannot place a Beethro, so we'll make a character that looks like him
            await self._editor_select_element(EDITOR_MONSTERS_TAB, EDITOR_CHARACTER)
            await self._editor_set_monster_direction(direction)
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
            await self._click(EDITOR_CHARACTER_WINDOW_SCROLL_UP)
            await self._click(EDITOR_CHARACTER_WINDOW_SCROLL_UP)
            await self._click(EDITOR_CHARACTER_WINDOW_FIRST_TYPE)
            await self._click(EDITOR_CHARACTER_WINDOW_VISIBLE_CHECKBOX)
            await self._click(EDITOR_CHARACTER_WINDOW_OKAY)

    async def editor_start_test_room(self, position, direction):
        """Start testing the room.

        Parameters
        ----------
        position
            The position to start in as a tuple (x, y).
        direction
            The direction to face when starting.
        """
        # Select the roach to make sure we can rotate monsters
        await self._editor_select_element(EDITOR_MONSTERS_TAB, EDITOR_ROACH)
        await self._editor_set_monster_direction(direction)
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

    async def editor_stop_test_room(self):
        """Stop testing the room."""
        pyautogui.press("esc")
        # Sleep to let the transition finish
        await asyncio.sleep(1)

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
        if step is not None:
            annotated_room = numpy.zeros(room_image.shape, numpy.uint8)
        room = Room()
        for (x, y), tile in tiles.items():
            start_x = x * TILE_SIZE
            end_x = (x + 1) * TILE_SIZE
            start_y = y * TILE_SIZE
            end_y = (y + 1) * TILE_SIZE
            tile_info, modified_tile = classify_tile(tile, step)
            room.set_tile((x, y), tile_info)
            if step is not None:
                annotated_room[start_y:end_y, start_x:end_x] = modified_tile
        visual_info["room"] = room

        if step is not None:
            visual_info["image"] = annotated_room
            return visual_info

        # If no step is specified, just don't include an image
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

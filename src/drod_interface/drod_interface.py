import numpy
import pyautogui

from common import (
    ROOM_WIDTH_IN_TILES,
    ROOM_HEIGHT_IN_TILES,
    Action,
    ImageProcessingStep,
    UserError,
    Element,
    Direction,
    Room,
)
from .classify import classify_tile
from .image_processing import (
    find_color,
    find_horizontal_lines,
)

OVERLAY_COLOR = (0, 255, 0)
OVERLAY_WIDTH = 5

DROD_WINDOW_WIDTH = 1024
DROD_WINDOW_HEIGHT = 768
ROOM_UPPER_EDGE_COLOR = (32, 60, 74)  # Also known as #203c4a
ROOM_UPPER_EDGE_LENGTH = 838
ROOM_UPPER_EDGE_START_X = 162
ROOM_UPPER_EDGE_START_Y = 39

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


class DrodInterface:
    def __init__(self):
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
        visual_info = await self.get_view(step=ImageProcessingStep.CROP_ROOM)
        self.origin_x = visual_info["origin_x"]
        self.origin_y = visual_info["origin_y"]
        await self._click((3, 3))
        # Let's use raw clicks here instead of editor_select_element().
        # The latter depend on the state being set up.
        if editor:
            await self._click(EDITOR_ROOM_PIECES_TAB)
            # Check whether the wall is normal or hard
            await self._click(EDITOR_WALL)
            self.editor_selected_element[EDITOR_ROOM_PIECES_TAB] = EDITOR_WALL
            image = (await self.get_view(step=ImageProcessingStep.CROP_WINDOW))["image"]
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
            image = (await self.get_view(step=ImageProcessingStep.CROP_WINDOW))["image"]
            while image[26, 140, 0] != 240:  # The roach's eye when facing SE
                pyautogui.press("q")
                image = (await self.get_view(step=ImageProcessingStep.CROP_WINDOW))[
                    "image"
                ]
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
            x=self.origin_x + ROOM_UPPER_EDGE_START_X + TILE_SIZE * 1.5,
            y=self.origin_y + ROOM_UPPER_EDGE_START_Y + TILE_SIZE * 1.5,
        )
        pyautogui.dragRel(
            xOffset=(ROOM_WIDTH_IN_TILES - 3) * TILE_SIZE,
            yOffset=(ROOM_HEIGHT_IN_TILES - 3) * TILE_SIZE,
            button="right",
        )

    async def editor_place_element(self, element, position, end_position=None):
        if element == Element.WALL:
            await self._editor_select_element(EDITOR_ROOM_PIECES_TAB, EDITOR_WALL)
        elif element == Element.CONQUER_TOKEN:
            await self._editor_select_element(EDITOR_ITEMS_TAB, EDITOR_TOKEN)
            # Click it again to bring up the menu, and select it
            await self._click(EDITOR_TOKEN)
            await self._click(EDITOR_CONQUER_TOKEN_IN_MENU)
        else:
            raise RuntimeError(f"Unknown element {element}")
        if end_position is None:
            await self._click(
                (
                    ROOM_UPPER_EDGE_START_X + (position[0] + 0.5) * TILE_SIZE,
                    ROOM_UPPER_EDGE_START_Y + (position[1] + 0.5) * TILE_SIZE,
                )
            )
        else:
            pyautogui.moveTo(
                x=self.origin_x
                + ROOM_UPPER_EDGE_START_X
                + TILE_SIZE * (position[0] + 0.5),
                y=self.origin_y
                + ROOM_UPPER_EDGE_START_Y
                + TILE_SIZE * (position[1] + 0.5),
            )
            pyautogui.dragRel(
                xOffset=(end_position[0] - position[0]) * TILE_SIZE,
                yOffset=(end_position[1] - position[1]) * TILE_SIZE,
            )

    async def get_view(self, step=None):
        visual_info = {}
        raw_image = numpy.array(pyautogui.screenshot())
        if step == ImageProcessingStep.SCREENSHOT:
            visual_info["image"] = raw_image
            return visual_info

        # == Identify the DROD window and room ==

        # Try finding the upper edge of the room, which is a long line of constant color
        correct_color = find_color(raw_image, ROOM_UPPER_EDGE_COLOR)
        if step == ImageProcessingStep.FIND_UPPER_EDGE_COLOR:
            visual_info["image"] = correct_color
            return visual_info

        lines = find_horizontal_lines(correct_color, ROOM_UPPER_EDGE_LENGTH)
        if step == ImageProcessingStep.FIND_UPPER_EDGE_LINE:
            # We can't show the line coordinates directly, so we'll overlay lines on
            # the screenshot
            with_lines = raw_image.copy()
            for (start_x, start_y, end_x, _) in lines:
                # Since we're only dealing with horizontal lines, we can do the overlay
                # by indexing the array directly
                with_lines[
                    start_y : start_y + OVERLAY_WIDTH, start_x:end_x, :
                ] = OVERLAY_COLOR
            visual_info["image"] = with_lines
            return visual_info

        if len(lines) > 1:
            raise UserError("Cannot identify DROD window, too many candidate lines")
        elif len(lines) == 0:
            raise UserError("Cannot identify DROD window, is it open and unblocked?")
        line_start_x = lines[0][0]
        line_start_y = lines[0][1]
        window_start_x = line_start_x - ROOM_UPPER_EDGE_START_X
        window_start_y = line_start_y - ROOM_UPPER_EDGE_START_Y
        window_end_x = window_start_x + DROD_WINDOW_WIDTH
        window_end_y = window_start_y + DROD_WINDOW_HEIGHT
        drod_window = raw_image[
            window_start_y:window_end_y,
            window_start_x:window_end_x,
            :,
        ]
        visual_info["origin_x"] = window_start_x
        visual_info["origin_y"] = window_start_y
        if step == ImageProcessingStep.CROP_WINDOW:
            visual_info["image"] = drod_window
            return visual_info

        room_start_x = ROOM_UPPER_EDGE_START_X + 1
        room_end_x = room_start_x + ROOM_WIDTH_IN_TILES * TILE_SIZE
        room_start_y = ROOM_UPPER_EDGE_START_Y + 1
        room_end_y = room_start_y + ROOM_HEIGHT_IN_TILES * TILE_SIZE
        room_image = drod_window[room_start_y:room_end_y, room_start_x:room_end_x, :]

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

import numpy
import pyautogui

from common import Action, ImageProcessingStep, UserError
from .classify import classify_tile
from .image_processing import (
    find_color,
    find_horizontal_lines,
    pil_to_array,
    array_to_pil,
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
ROOM_WIDTH_IN_TILES = 38
ROOM_HEIGHT_IN_TILES = 32

EDITOR_ROOM_PIECES_TAB = (24, 20)
EDITOR_FLOOR_CONTROLS_TAB = (60, 20)
EDITOR_ITEMS_TAB = (100, 20)
EDITOR_MONSTERS_TAB = (135, 20)

EDITOR_FLOOR = (25, 300)

EDITOR_FORCE_ARROW = (30, 50)
EDITOR_CHECKPOINT = (120, 50)
EDITOR_WALL_LIGHT = (25, 85)


class DrodInterface:
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

    async def focus_window(self, visual_info):
        await self._click_in_window(visual_info, 3, 3)

    async def _click_in_window(self, visual_info, x, y):
        pyautogui.click(x=visual_info["x_origin"] + x, y=visual_info["y_origin"] + y)

    async def editor_clear_room(self, visual_info):
        await self._click_in_window(visual_info, *EDITOR_ROOM_PIECES_TAB)
        # Select the normal floor, so clearing doesn't use mosaic floors
        await self._click_in_window(visual_info, *EDITOR_FLOOR)
        await self._editor_clear_layer(visual_info)

        await self._click_in_window(visual_info, *EDITOR_FLOOR_CONTROLS_TAB)
        # This tab contains three layers (disregarding level entrances),
        # which need to be cleared separately
        await self._click_in_window(visual_info, *EDITOR_FORCE_ARROW)
        await self._editor_clear_layer(visual_info)
        await self._click_in_window(visual_info, *EDITOR_CHECKPOINT)
        await self._editor_clear_layer(visual_info)
        await self._click_in_window(visual_info, *EDITOR_WALL_LIGHT)
        await self._editor_clear_layer(visual_info)

        await self._click_in_window(visual_info, *EDITOR_ITEMS_TAB)
        await self._editor_clear_layer(visual_info)

        await self._click_in_window(visual_info, *EDITOR_MONSTERS_TAB)
        await self._editor_clear_layer(visual_info)

    async def _editor_clear_layer(self, visual_info):
        pyautogui.moveTo(
            x=visual_info["x_origin"] + ROOM_UPPER_EDGE_START_X + TILE_SIZE * 1.5,
            y=visual_info["y_origin"] + ROOM_UPPER_EDGE_START_Y + TILE_SIZE * 1.5,
        )
        pyautogui.dragRel(
            xOffset=(ROOM_WIDTH_IN_TILES - 3) * TILE_SIZE,
            yOffset=(ROOM_HEIGHT_IN_TILES - 3) * TILE_SIZE,
            button="right",
        )

    async def get_view(self, step=None):
        visual_info = {}
        raw_image = pil_to_array(pyautogui.screenshot())
        if step == ImageProcessingStep.SCREENSHOT:
            visual_info["image"] = array_to_pil(raw_image)
            return visual_info

        # == Identify the DROD window and room ==

        # Try finding the upper edge of the room, which is a long line of constant color
        correct_color = find_color(raw_image, ROOM_UPPER_EDGE_COLOR)
        if step == ImageProcessingStep.FIND_UPPER_EDGE_COLOR:
            visual_info["image"] = array_to_pil(correct_color)
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
            visual_info["image"] = array_to_pil(with_lines)
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
        visual_info["x_origin"] = window_start_x
        visual_info["y_origin"] = window_start_y
        if step == ImageProcessingStep.CROP_WINDOW:
            visual_info["image"] = array_to_pil(drod_window)
            return visual_info

        room_start_x = ROOM_UPPER_EDGE_START_X + 1
        room_end_x = room_start_x + ROOM_WIDTH_IN_TILES * TILE_SIZE
        room_start_y = ROOM_UPPER_EDGE_START_Y + 1
        room_end_y = room_start_y + ROOM_HEIGHT_IN_TILES * TILE_SIZE
        room = drod_window[room_start_y:room_end_y, room_start_x:room_end_x, :]

        if step == ImageProcessingStep.CROP_ROOM:
            visual_info["image"] = array_to_pil(room)
            return visual_info

        # == Extract and classify tiles in the room ==

        tiles = {}
        for x in range(ROOM_WIDTH_IN_TILES):
            for y in range(ROOM_HEIGHT_IN_TILES):
                start_x = x * TILE_SIZE
                end_x = (x + 1) * TILE_SIZE
                start_y = y * TILE_SIZE
                end_y = (y + 1) * TILE_SIZE
                tiles[(x, y)] = room[start_y:end_y, start_x:end_x, :]
        visual_info["tiles"] = tiles

        if step == ImageProcessingStep.EXTRACT_TILES:
            # We can't show anything more interesting here
            visual_info["image"] = array_to_pil(room)
            return visual_info

        # If a step is specified, we will return an image composed of modified tiles
        if step is not None:
            annotated_room = numpy.zeros(room.shape, numpy.uint8)
        room_entities = {}
        for (x, y), tile in tiles.items():
            start_x = x * TILE_SIZE
            end_x = (x + 1) * TILE_SIZE
            start_y = y * TILE_SIZE
            end_y = (y + 1) * TILE_SIZE
            room_entities[(x, y)], modified_tile = classify_tile(tile, step)
            if step is not None:
                annotated_room[start_y:end_y, start_x:end_x] = modified_tile
        visual_info["entities"] = room_entities

        if step is not None:
            visual_info["image"] = array_to_pil(annotated_room)
            return visual_info

        # If no step is specified, just don't include an image
        return visual_info

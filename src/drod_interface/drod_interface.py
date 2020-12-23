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

TILE_WIDTH = 22
TILE_HEIGHT = 22
ROOM_WIDTH_IN_TILES = 38
ROOM_HEIGHT_IN_TILES = 32


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
        pyautogui.moveTo(x=visual_info["x_origin"] + 3, y=visual_info["y_origin"] + 3)
        pyautogui.click()

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
        room_end_x = room_start_x + ROOM_WIDTH_IN_TILES * TILE_WIDTH
        room_start_y = ROOM_UPPER_EDGE_START_Y + 1
        room_end_y = room_start_y + ROOM_HEIGHT_IN_TILES * TILE_HEIGHT
        room = drod_window[room_start_y:room_end_y, room_start_x:room_end_x, :]

        if step == ImageProcessingStep.CROP_ROOM:
            visual_info["image"] = array_to_pil(room)
            return visual_info

        # == Classify stuff in the room ==

        room_entities = {}
        # If a step is specified, we will probably return a modified image
        if step is not None:
            annotated_room = room.copy()
        for x in range(ROOM_WIDTH_IN_TILES):
            for y in range(ROOM_HEIGHT_IN_TILES):
                start_x = x * TILE_WIDTH
                end_x = (x + 1) * TILE_WIDTH
                start_y = y * TILE_HEIGHT
                end_y = (y + 1) * TILE_HEIGHT
                tile = room[start_y:end_y, start_x:end_x, :]
                room_entities[(x, y)], modified_tile = classify_tile(tile, step)
                if step is not None:
                    annotated_room[start_y:end_y, start_x:end_x] = modified_tile
        visual_info["entities"] = room_entities

        if step is not None:
            visual_info["image"] = array_to_pil(annotated_room)
            return visual_info

        # If no step is specified, just don't include an image
        return visual_info

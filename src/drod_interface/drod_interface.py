import pyautogui

from common import Action, ImageProcessingStep
from .image_processing import (
    find_color,
    find_horizontal_lines,
    pil_to_array,
    array_to_pil,
)

OVERLAY_COLOR = (0, 255, 0)
OVERLAY_WIDTH = 5

# Also known as #203c4a
ROOM_UPPER_EDGE_COLOR = (32, 60, 74)
ROOM_UPPER_EDGE_LENGTH = 838


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

    async def get_view(self, step):
        raw_image = pil_to_array(pyautogui.screenshot())
        if step == ImageProcessingStep.SCREENSHOT:
            return array_to_pil(raw_image)

        # == Identify the DROD window ==

        # Try finding the upper edge of the room, which is a long line of constant color
        correct_color = find_color(raw_image, ROOM_UPPER_EDGE_COLOR)
        if step == ImageProcessingStep.FIND_UPPER_EDGE_COLOR:
            return array_to_pil(correct_color)

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
            return array_to_pil(with_lines)

        raise RuntimeError(f"Unknown step {step}")

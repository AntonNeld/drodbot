import pyautogui

from common import Action, ImageProcessingStep
from .image_processing import (
    find_color,
    ROOM_UPPER_EDGE_COLOR,
    pil_to_array,
    array_to_pil,
)


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

        # Try finding the upper edge of the room, which is a long line of constant color
        correct_color = find_color(raw_image, ROOM_UPPER_EDGE_COLOR)
        if step == ImageProcessingStep.FIND_UPPER_EDGE_COLOR:
            return array_to_pil(correct_color)

        raise RuntimeError(f"Unknown step {step}")

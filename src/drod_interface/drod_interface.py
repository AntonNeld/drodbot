import pyautogui

from common import Action, ImageProcessingStep


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

    async def get_view(self, step=None):
        raw_image = pyautogui.screenshot()
        if step == ImageProcessingStep.SCREENSHOT:
            return raw_image

        rotated_image = raw_image.rotate(45)
        return rotated_image

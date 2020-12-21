import pyautogui

from common import Action


class DrodInterface:
    def do_action(self, action):
        if action == Action.SW:
            pyautogui.press("num1")
        elif action == Action.S:
            pyautogui.press("num2")
        elif action == Action.SE:
            pyautogui.press("num3")
        elif action == Action.W:
            pyautogui.press("num4")
        elif action == Action.WAIT:
            pyautogui.press("num5")
        elif action == Action.E:
            pyautogui.press("num6")
        elif action == Action.NW:
            pyautogui.press("num7")
        elif action == Action.N:
            pyautogui.press("num8")
        elif action == Action.NE:
            pyautogui.press("num9")
        elif action == Action.CCW:
            pyautogui.press("q")
        elif action == Action.CW:
            pyautogui.press("w")

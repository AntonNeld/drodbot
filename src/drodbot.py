import time
import random

import pyautogui

from drod_interface import DrodInterface
from common import Action

if __name__ == "__main__":
    drod = DrodInterface()
    pyautogui.alert(
        "I will now move randomly. Focus the DROD window,"
        " then focus this window and press OK."
        " Move the mouse to the corner of the screen to exit."
    )
    try:
        while True:
            time.sleep(0.1)
            action = random.choice(list(Action))
            drod.do_action(action)
    except pyautogui.FailSafeException:
        print("Bye!")

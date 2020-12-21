import time
import tkinter
import random

import pyautogui

from drod_interface import DrodInterface
from gui_app import GuiApp
from common import Action

if __name__ == "__main__":
    drod = DrodInterface()
    window = tkinter.Tk()
    app = GuiApp(root=window)
    app.mainloop()
    try:
        while True:
            time.sleep(0.1)
            action = random.choice(list(Action))
            drod.do_action(action)
    except (pyautogui.FailSafeException, KeyboardInterrupt):
        print("Bye!")

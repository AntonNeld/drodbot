import time
import random

import pyautogui


if __name__ == "__main__":
    pyautogui.alert(
        "I will now move randomly. Focus the DROD window,"
        " then focus this window and press OK."
        " Move the mouse to the corner of the screen to exit."
    )
    try:
        while True:
            time.sleep(0.1)
            key = random.choice(
                (
                    "q",
                    "w",
                    "num1",
                    "num2",
                    "num3",
                    "num4",
                    "num5",
                    "num6",
                    "num7",
                    "num8",
                    "num9",
                )
            )
            pyautogui.press(key)
    except pyautogui.FailSafeException:
        print("Bye!")

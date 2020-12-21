import pyautogui

if __name__ == "__main__":
    print("I will now move the mouse a bit")
    start_x, start_y = pyautogui.position()
    for dx, dy in [(40, 23), (-100, 0), (10, 84), (0, 0)]:
        pyautogui.moveTo(
            start_x + dx, start_y + dy, duration=1, tween=pyautogui.easeInOutQuad
        )

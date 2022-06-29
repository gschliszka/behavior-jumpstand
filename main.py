import pyautogui as pyg  # Import pyautogui
import time             # Import Time
import tkinter as tk    # GUI
from stimuli import StaticBars, core, event
from constant import *


def mouse_pos():
    try:
        while True:  # Start loop
            x, y = pyg.position()
            if 0 <= x <= 1920 and 0 <= y <= 1080:
                print(f"X: {x}, Y: {y} --> HDMI-1")
            else:
                print(f"X: {x}, Y: {y} --> HDMI-2")
            time.sleep(0.5)
    except KeyboardInterrupt:
        print('\nDone')


if __name__ == '__main__':
    left = StaticBars(params={'monitor': 'Samsung_LE40C530', 'screen': 0,
                              'distance': 40, 'color_bg': 0,
                              'spatial_frequency': 0.1, 'contrast': 1, 'orientation': 'horizontal',
                              'num_bars': 2, 'color_bar': (1, 1, 1)})

    right = StaticBars(params={'monitor': 'Small_LG', 'screen': 1,
                               'distance': 40, 'color_bg': 0,
                               'spatial_frequency': 0.1, 'contrast': 1, 'orientation': 'horizontal',
                               'num_bars': 2, 'color_bar': (1, 1, 1)})

    for i in range(4):
        print(CAT)      # command Ard to get in CAT state
        # read some serial input
        # while input() != "cat's blocking IRgate for given time":
        #   wait
        if i % 2 == 0:          # for testing, it will be randomized
            left.stimulate()
        else:
            right.stimulate()
        # wait for the cat to decide, monitoring mouse click event and position to check whether the decision was
        # correct or not
        t = time.time()
        _resp = False
        _left = False
        while time.time()-t < 3:
            if event.getKeys(keyList=["escape"]):  # or self.endExpNow
                print("Escape key detected. Quitting!")
                core.quit()

            if left.mouse.getPressed() != [0, 0, 0] or right.mouse.getPressed() != [0, 0, 0]:
                x, y = pyg.position()
                if (0 <= x <= left.mon.currentCalib['sizePix'][0] and
                    0 <= y <= left.mon.currentCalib['sizePix'][1]):
                    _left = True
                if left.active and _left:
                    _resp = True
                if right.active and not _left:
                    _resp = True
                #rint(f'{i}. trial, response: {_resp}')
                break
                """
                x, y = pyg.position()
                print(x,y)
                print(left.mouse.getPressed())
                print(right.mouse.getPressed())
                break
                """
        print(f'{i}. trial, response: {_resp}')

        left.end()
        right.end()
        # wait to the cat place back to the table
        time.sleep(3)


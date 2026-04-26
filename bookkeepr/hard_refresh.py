"""Hard refresh Chrome"""
import pyautogui
import time

# Hard refresh
pyautogui.keyDown('ctrl')
pyautogui.keyDown('f5')
pyautogui.keyUp('f5')
pyautogui.keyUp('ctrl')

time.sleep(5)

# Scroll to top
pyautogui.scroll(10, 960, 600)
time.sleep(1)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\after_hard_refresh.png")
print("After hard refresh screenshot saved")

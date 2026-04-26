"""Check URL bar"""
import pyautogui
import time

# Click URL bar
pyautogui.click(600, 60)
time.sleep(1)

# Select all and copy
pyautogui.keyDown('ctrl')
pyautogui.keyDown('a')
pyautogui.keyUp('a')
pyautogui.keyUp('ctrl')
time.sleep(0.3)

pyautogui.keyDown('ctrl')
pyautogui.keyDown('c')
pyautogui.keyUp('c')
pyautogui.keyUp('ctrl')
time.sleep(0.3)

# Click elsewhere
pyautogui.click(960, 300)
time.sleep(0.5)

# Take screenshot of URL bar area
screenshot = pyautogui.screenshot(region=(400, 40, 800, 50))
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\url_bar_shot.png")
print("URL bar screenshot saved")

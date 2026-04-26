"""Navigate using keyboard"""
import pyautogui
import time

# Press Escape to close dialog
pyautogui.keyDown('esc')
pyautogui.keyUp('esc')
time.sleep(1)

# Click on BookKeepr tab
pyautogui.click(200, 30)
time.sleep(2)

# Hard refresh
pyautogui.keyDown('ctrl')
pyautogui.keyDown('f5')
pyautogui.keyUp('f5')
pyautogui.keyUp('ctrl')

time.sleep(5)

screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\navigated_keyboard.png"
screenshot.save(path)
print("Screenshot saved")

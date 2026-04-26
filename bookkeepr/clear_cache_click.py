"""Clear Chrome cache and test"""
import pyautogui
import time
import subprocess

# Open Chrome dev tools to clear cache
pyautogui.keyDown('ctrl')
pyautogui.keyDown('shift')
pyautogui.keyDown('delete')
pyautogui.keyUp('delete')
pyautogui.keyUp('shift')
pyautogui.keyUp('ctrl')

time.sleep(2)

# Click Clear Data
pyautogui.click(1100, 700)
time.sleep(3)

# Now test clicking Transactions
pyautogui.click(170, 270)
time.sleep(4)

screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\after_clear_cache.png"
screenshot.save(path)
print("Screenshot saved after clearing cache")

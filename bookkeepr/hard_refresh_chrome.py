"""Hard refresh Chrome"""
import pyautogui
import time

# Hard refresh
pyautogui.keyDown('ctrl')
pyautogui.keyDown('shift')
pyautogui.keyDown('r')
pyautogui.keyUp('r')
pyautogui.keyUp('shift')
pyautogui.keyUp('ctrl')

time.sleep(5)
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\chrome_refreshed.png"
screenshot.save(path)
print("Chrome refreshed")

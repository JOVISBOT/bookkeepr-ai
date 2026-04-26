"""Open browser console and check for errors"""
import pyautogui
import time

# Open dev console
pyautogui.keyDown('f12')
pyautogui.keyUp('f12')
time.sleep(2)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\console_check.png")
print("Console screenshot saved")

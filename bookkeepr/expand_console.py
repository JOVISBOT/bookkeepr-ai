"""Expand console to see errors"""
import pyautogui
import time

# Click on the issue
pyautogui.click(1250, 880)
time.sleep(2)

# Take screenshot
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\console_expanded.png")
print("Console expanded screenshot saved")

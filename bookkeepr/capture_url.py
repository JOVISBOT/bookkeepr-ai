"""Capture URL bar"""
import pyautogui
import time

# Click on URL bar and screenshot
pyautogui.click(500, 60)
time.sleep(1)

screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\url_screenshot.png"
screenshot.save(path)
print("URL screenshot saved")

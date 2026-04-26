"""Show full URL bar"""
import pyautogui
import time

# Take full screenshot showing URL bar
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\full_browser.png")
print("Full browser screenshot saved")

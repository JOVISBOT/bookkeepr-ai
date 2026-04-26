"""Scroll down to see charts"""
import pyautogui
import time

# Scroll down
pyautogui.scroll(-8, 960, 600)
time.sleep(2)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\scroll_down_result.png")
print("Screenshot saved")

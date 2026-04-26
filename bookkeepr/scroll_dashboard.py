"""Scroll down to see charts"""
import pyautogui
import time

# Scroll down
pyautogui.scroll(-5, 960, 600)
time.sleep(2)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\dashboard_scrolled.png")
print("Dashboard scrolled screenshot saved")

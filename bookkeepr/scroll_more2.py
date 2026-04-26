"""Scroll down to see Financial Overview"""
import pyautogui
import time

# Scroll down more
pyautogui.scroll(-10, 960, 600)
time.sleep(2)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\financial_overview.png")
print("Financial Overview screenshot saved")

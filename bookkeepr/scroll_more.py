"""Scroll down more to see charts"""
import pyautogui
import time

# Scroll down multiple times
for i in range(5):
    pyautogui.scroll(-5, 960, 600)
    time.sleep(1)
    screenshot = pyautogui.screenshot()
    screenshot.save(rf"C:\Users\jovis\.openclaw\workspace\bookkeepr\scroll_{i}.png")
    print(f"Scroll {i} screenshot saved")

print("Done scrolling")

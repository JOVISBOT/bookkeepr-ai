"""Find charts section"""
import pyautogui
import time

# Scroll down to find Financial Overview
for i in range(10):
    pyautogui.scroll(-2, 960, 600)
    time.sleep(1)
    screenshot = pyautogui.screenshot()
    screenshot.save(rf"C:\Users\jovis\.openclaw\workspace\bookkeepr\chart_search_{i}.png")
    print(f"Screenshot {i} saved")

print("Done searching")

"""Show charts at top"""
import pyautogui
import time

# Scroll to top first
pyautogui.scroll(10, 960, 600)
time.sleep(1)

# Then scroll down a bit to see charts section
pyautogui.scroll(-4, 960, 600)
time.sleep(2)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\charts_view.png")
print("Charts view screenshot saved")

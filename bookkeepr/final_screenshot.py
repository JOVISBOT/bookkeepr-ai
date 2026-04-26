"""Take final screenshot of BookKeepr dashboard"""
import pyautogui
import time

# Scroll down to see all content
pyautogui.scroll(-3, 960, 600)
time.sleep(1)

# Take screenshot
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\screenshot_final_dashboard.png"
screenshot.save(path)
print(f"Final screenshot saved: {path}")

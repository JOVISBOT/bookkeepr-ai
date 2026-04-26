"""Check console for errors"""
import pyautogui
import time

# Click on Console tab
pyautogui.click(1150, 850)
time.sleep(2)

# Take screenshot
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\console_errors.png")
print("Console errors screenshot saved")

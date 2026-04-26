"""Show clean charts view"""
import pyautogui
import time

# Close console
pyautogui.keyDown('f12')
pyautogui.keyUp('f12')
time.sleep(2)

# Scroll down to see charts
pyautogui.scroll(-6, 960, 600)
time.sleep(2)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\charts_clean.png")
print("Clean charts screenshot saved")

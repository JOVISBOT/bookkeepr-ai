"""Switch to console tab"""
import pyautogui
import time

# Click on Console tab
pyautogui.click(1150, 850)
time.sleep(2)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\console_tab.png")
print("Console tab screenshot saved")

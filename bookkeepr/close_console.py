"""Close console and take screenshot"""
import pyautogui
import time

# Close dev console
pyautogui.keyDown('f12')
pyautogui.keyUp('f12')
time.sleep(2)

# Scroll to top
pyautogui.scroll(10, 960, 600)
time.sleep(1)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\no_console.png")
print("Screenshot without console saved")

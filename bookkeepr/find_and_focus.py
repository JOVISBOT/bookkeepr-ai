"""Find and focus Chrome"""
import pyautogui
import time

# Try to find Chrome by pressing Alt+Tab multiple times
for i in range(10):
    pyautogui.keyDown('alt')
    pyautogui.keyDown('tab')
    pyautogui.keyUp('tab')
    pyautogui.keyUp('alt')
    time.sleep(0.5)

# Take screenshot
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\alt_tab_test.png"
screenshot.save(path)
print("Screenshot saved")

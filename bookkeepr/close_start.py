"""Close start menu and find Chrome"""
import pyautogui
import time

# Press Escape to close start menu
pyautogui.keyDown('esc')
pyautogui.keyUp('esc')
time.sleep(0.5)

# Now try to find Chrome window by pressing Alt+Tab
pyautogui.keyDown('alt')
pyautogui.keyDown('tab')
pyautogui.keyUp('tab')
pyautogui.keyUp('alt')
time.sleep(1)

# Take screenshot
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\screenshot_alt_tab.png"
screenshot.save(path)
print(f"Screenshot saved: {path}")

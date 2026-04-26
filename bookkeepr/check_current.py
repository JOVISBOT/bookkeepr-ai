"""Check current URL and navigate to BookKeepr"""
import pyautogui
import time

# Take screenshot of current state
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\screenshot_current_state.png"
screenshot.save(path)

# Try to find Chrome window by clicking at different positions
# Chrome icon in taskbar is around x=570, y=1050
pyautogui.click(570, 1050)
time.sleep(2)

# Take screenshot after clicking
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\screenshot_after_click.png"
screenshot.save(path)
print(f"Screenshot saved: {path}")

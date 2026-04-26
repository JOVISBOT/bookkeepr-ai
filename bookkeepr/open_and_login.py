"""Open Chrome, navigate to BookKeepr, and login"""
import subprocess
import pyautogui
import time

# Open Chrome
subprocess.Popen(['start', 'chrome', '--new-window', 'http://localhost:5000/auth/login'], shell=True)
time.sleep(5)

# Fill in login form
pyautogui.click(960, 450)
time.sleep(0.5)
pyautogui.typewrite("test@bookkeepr.ai")
time.sleep(0.3)

pyautogui.keyDown('tab')
pyautogui.keyUp('tab')
time.sleep(0.3)

pyautogui.typewrite("password123")
time.sleep(0.3)

pyautogui.keyDown('return')
pyautogui.keyUp('return')
time.sleep(5)

# Take screenshot
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\screenshot_blue_dashboard.png"
screenshot.save(path)
print(f"Screenshot saved: {path}")

"""
Show BookKeepr progress - Screenshot capture
"""
import subprocess
import time
import pyautogui

# Kill Chrome
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
time.sleep(2)

# Open Chrome with dashboard
subprocess.Popen([
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    '--new-window',
    'http://localhost:5002/'
])

time.sleep(5)

# Take screenshot
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\progress_live.png")
print("Screenshot saved: progress_live.png")

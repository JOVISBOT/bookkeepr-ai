"""Open new Chrome window"""
import subprocess
import time
import pyautogui

# Kill any existing Chrome
import os
os.system('taskkill /F /IM chrome.exe 2>nul')
time.sleep(2)

# Open Chrome with BookKeepr
subprocess.Popen([
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    '--new-window',
    'http://localhost:5000/'
])

time.sleep(5)

# Take screenshot
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\new_chrome_window.png"
screenshot.save(path)
print("New Chrome screenshot saved")

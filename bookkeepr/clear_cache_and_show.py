"""Clear cache and show dashboard"""
import subprocess
import time
import pyautogui

# Kill Chrome
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
time.sleep(2)

# Delete Chrome cache
import shutil
import os

cache_path = os.path.expanduser(r'~\AppData\Local\Google\Chrome\User Data\Default\Cache')
if os.path.exists(cache_path):
    shutil.rmtree(cache_path)
    print("Cache cleared")

# Open Chrome with clear cache flag
subprocess.Popen([
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    '--new-window',
    '--disable-cache',
    '--disk-cache-size=1',
    'http://localhost:5000/auth/login'
])

time.sleep(5)

# Login
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
time.sleep(6)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\cleared_cache_dashboard.png")
print("Cleared cache dashboard screenshot saved")

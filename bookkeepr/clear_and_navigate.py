"""Clear cache and navigate"""
import subprocess
import time
import pyautogui

# Open Chrome settings to clear cache
subprocess.Popen([
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'chrome://settings/clearBrowserData'
])

time.sleep(3)

# Click "Cached images and files" checkbox
pyautogui.click(1000, 500)
time.sleep(0.5)

# Click Clear data
pyautogui.click(1100, 800)
time.sleep(3)

# Now navigate to transactions
subprocess.Popen([
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    'http://localhost:5000/dashboard/transactions'
])

time.sleep(5)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\after_clear.png")
print("Screenshot saved after clearing cache")

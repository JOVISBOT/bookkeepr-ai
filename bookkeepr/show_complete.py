"""Show complete dashboard"""
import subprocess
import time
import pyautogui

# Kill Chrome
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
time.sleep(2)

# Open Chrome
subprocess.Popen([
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    '--new-window',
    'http://localhost:5000/'
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

# Screenshot full page
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\complete_dashboard.png")
print("Complete dashboard saved")

# Scroll to see charts
pyautogui.scroll(-5, 960, 600)
time.sleep(2)
screenshot2 = pyautogui.screenshot()
screenshot2.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\complete_dashboard_scrolled.png")
print("Scrolled dashboard saved")

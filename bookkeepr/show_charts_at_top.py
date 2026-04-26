"""Scroll to top and capture charts"""
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
time.sleep(8)

# Press Home key to scroll to top
pyautogui.keyDown('home')
pyautogui.keyUp('home')
time.sleep(2)

# Take screenshot of the charts at the top
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\charts_at_top.png")
print("Charts at top screenshot saved")

# Scroll down a bit to see both charts
pyautogui.scroll(-3, 960, 600)
time.sleep(1)
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\charts_scrolled.png")
print("Charts scrolled screenshot saved")

"""Check for JavaScript errors"""
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

# Open console
pyautogui.keyDown('f12')
pyautogui.keyUp('f12')
time.sleep(2)

# Click console tab
pyautogui.click(1150, 850)
time.sleep(1)

# Clear console
pyautogui.keyDown('ctrl')
pyautogui.keyDown('l')
pyautogui.keyUp('l')
pyautogui.keyUp('ctrl')
time.sleep(1)

# Reload page
pyautogui.keyDown('f5')
pyautogui.keyUp('f5')
time.sleep(5)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\js_errors.png")
print("JS errors screenshot saved")

"""Open incognito window"""
import subprocess
import time
import pyautogui

# Open Chrome incognito
subprocess.Popen([
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    '--incognito',
    'http://localhost:5000/dashboard/transactions'
])

time.sleep(5)

# Login
pyautogui.click(960, 400)
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

screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\incognito_result.png"
screenshot.save(path)
print("Incognito screenshot saved")

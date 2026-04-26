"""Focus Chrome and test links"""
import pyautogui
import time
import subprocess

# Find Chrome window
subprocess.run(['powershell', '-Command', '(New-Object -ComObject WScript.Shell).AppActivate("Google Chrome")'], capture_output=True)
time.sleep(1)

# Now take screenshots
pyautogui.keyDown('alt')
pyautogui.keyDown('tab')
pyautogui.keyUp('tab')
pyautogui.keyUp('alt')
time.sleep(1)

screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\chrome_focus.png"
screenshot.save(path)
print("Chrome screenshot saved")

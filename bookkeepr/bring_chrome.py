"""Bring Chrome to front and screenshot"""
import subprocess
import time
import pyautogui

# Use powershell to bring Chrome to front
subprocess.run(['powershell', '-Command', '$wshell = New-Object -ComObject WScript.Shell; $wshell.AppActivate("Google Chrome")'], capture_output=True)
time.sleep(2)

# Take screenshot
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\chrome_front.png")
print("Chrome front screenshot saved")

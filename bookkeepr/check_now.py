"""Check current screen state"""
import pyautogui

# Take screenshot to see what's on screen
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\debug_screen.png")
print("Screenshot saved - checking what's on screen")

# Get screen dimensions
width, height = pyautogui.size()
print(f"Screen size: {width}x{height}")

# Check if Chrome is open
import subprocess
result = subprocess.run(['tasklist'], capture_output=True, text=True)
if 'chrome.exe' in result.stdout:
    print("Chrome is running")
else:
    print("Chrome is NOT running")

# Check server
import urllib.request
try:
    response = urllib.request.urlopen('http://localhost:5000/', timeout=5)
    print(f"Server responding: {response.status}")
except:
    print("Server NOT responding")

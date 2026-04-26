"""Test all pages"""
import pyautogui
import time
import subprocess

pages = [
    ("Accounts", "http://localhost:5000/dashboard/accounts", 170, 310),
    ("Reports", "http://localhost:5000/dashboard/reports", 170, 350),
    ("Settings", "http://localhost:5000/dashboard/settings", 170, 390)
]

for name, url, x, y in pages:
    # Navigate to page
    subprocess.Popen([
        r'C:\Program Files\Google\Chrome\Application\chrome.exe',
        url
    ])
    
    time.sleep(5)
    
    # Screenshot
    screenshot = pyautogui.screenshot()
    screenshot.save(rf"C:\Users\jovis\.openclaw\workspace\bookkeepr\page_{name.lower()}.png")
    print(f"{name} screenshot saved")
    
    time.sleep(2)

print("All pages tested!")

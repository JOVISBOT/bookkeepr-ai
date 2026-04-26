"""Show BookKeepr progress on screen"""
import subprocess
import time
import pyautogui

# Kill any existing Chrome
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
time.sleep(2)

# Open Chrome with BookKeepr
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

# Take screenshot of dashboard
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\progress_dashboard.png")
print("Dashboard screenshot saved")

# Now navigate through pages
pages = [
    ("/dashboard/transactions", "transactions"),
    ("/dashboard/accounts", "accounts"),
    ("/dashboard/reports", "reports"),
    ("/dashboard/settings", "settings")
]

for url, name in pages:
    # Navigate to page
    pyautogui.click(300, 50)  # Click URL bar
    time.sleep(0.5)
    pyautogui.typewrite(f"http://localhost:5000{url}")
    time.sleep(0.3)
    pyautogui.keyDown('return')
    pyautogui.keyUp('return')
    time.sleep(4)
    
    # Screenshot
    screenshot = pyautogui.screenshot()
    screenshot.save(rf"C:\Users\jovis\.openclaw\workspace\bookkeepr\progress_{name}.png")
    print(f"{name} page screenshot saved")

print("All progress screenshots captured!")

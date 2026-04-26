"""Kill all Chrome and open fresh"""
import subprocess
import time
import pyautogui

# Kill all Chrome
subprocess.run(['taskkill', '/F', '/IM', 'chrome.exe'], capture_output=True)
time.sleep(3)

# Open Chrome to login
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
time.sleep(5)

# Screenshot dashboard
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\fresh_dashboard.png"
screenshot.save(path)

# Now click on Transactions
pyautogui.click(170, 270)
time.sleep(4)

screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\fresh_transactions.png"
screenshot.save(path)

# Click on Accounts
pyautogui.click(170, 310)
time.sleep(4)

screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\fresh_accounts.png"
screenshot.save(path)

print("All screenshots saved")

"""Show live dashboard on screen"""
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

# Screenshot
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\live_dashboard.png")
print("Dashboard screenshot saved")

# Scroll to show AI Actions
pyautogui.scroll(-3, 960, 600)
time.sleep(2)
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\live_ai_actions.png")
print("AI Actions screenshot saved")

# Scroll to show transactions
pyautogui.scroll(-3, 960, 600)
time.sleep(2)
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\live_transactions.png")
print("Transactions screenshot saved")

print("\nDashboard screenshots captured!")
print("Check these files:")
print("1. live_dashboard.png - Financial Overview with charts")
print("2. live_ai_actions.png - AI Bookkeeping Actions")
print("3. live_transactions.png - Recent Transactions")

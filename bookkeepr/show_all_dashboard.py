"""Show complete dashboard"""
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

# Scroll through the entire page to show all sections
sections = [
    ("charts", "Financial Overview with Charts"),
    ("ai_actions", "AI Bookkeeping Actions"),
    ("transactions", "Recent Transactions")
]

for i, (name, desc) in enumerate(sections):
    screenshot = pyautogui.screenshot()
    screenshot.save(rf"C:\Users\jovis\.openclaw\workspace\bookkeepr\dashboard_{name}.png")
    print(f"Section {i+1}: {desc}")
    
    if i < len(sections) - 1:
        pyautogui.scroll(-5, 960, 600)
        time.sleep(2)

print("All dashboard sections captured!")

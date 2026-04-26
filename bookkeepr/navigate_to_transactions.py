"""Navigate to transactions URL directly"""
import pyautogui
import time

# Click URL bar
pyautogui.click(500, 60)
time.sleep(0.5)

# Select all
pyautogui.keyDown('ctrl')
pyautogui.keyDown('a')
pyautogui.keyUp('a')
pyautogui.keyUp('ctrl')
time.sleep(0.3)

# Type transactions URL
pyautogui.typewrite("http://localhost:5000/dashboard/transactions")
time.sleep(0.3)

# Press Enter
pyautogui.keyDown('return')
pyautogui.keyUp('return')
time.sleep(5)

screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\transactions_direct.png"
screenshot.save(path)
print("Transactions page screenshot saved")

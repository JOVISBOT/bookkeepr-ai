"""Test direct URL navigation"""
import pyautogui
import time

# Click on URL bar
pyautogui.click(600, 60)
time.sleep(0.5)

# Select all and type transactions URL
pyautogui.keyDown('ctrl')
pyautogui.keyDown('a')
pyautogui.keyUp('a')
pyautogui.keyUp('ctrl')
time.sleep(0.3)

pyautogui.typewrite("http://localhost:5000/dashboard/transactions")
time.sleep(0.3)
pyautogui.keyDown('return')
pyautogui.keyUp('return')
time.sleep(5)

# Screenshot
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\direct_transactions.png"
screenshot.save(path)
print("Direct URL screenshot saved")

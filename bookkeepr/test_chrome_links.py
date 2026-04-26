"""Test all links in Chrome"""
import pyautogui
import time

# Navigate to dashboard
pyautogui.click(500, 60)
time.sleep(0.5)
pyautogui.keyDown('ctrl')
pyautogui.keyDown('a')
pyautogui.keyUp('a')
pyautogui.keyUp('ctrl')
time.sleep(0.3)
pyautogui.typewrite("http://localhost:5000/")
time.sleep(0.3)
pyautogui.keyDown('return')
pyautogui.keyUp('return')
time.sleep(5)

# Take screenshot of dashboard
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\screenshot_test_1.png"
screenshot.save(path)
print("Dashboard screenshot saved")

# Click on Transactions
pyautogui.click(200, 250)
time.sleep(3)
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\screenshot_test_2.png"
screenshot.save(path)
print("Transactions screenshot saved")

# Click on Accounts
pyautogui.click(200, 290)
time.sleep(3)
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\screenshot_test_3.png"
screenshot.save(path)
print("Accounts screenshot saved")

# Click on Reports
pyautogui.click(200, 330)
time.sleep(3)
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\screenshot_test_4.png"
screenshot.save(path)
print("Reports screenshot saved")

# Click on Settings
pyautogui.click(200, 370)
time.sleep(3)
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\screenshot_test_5.png"
screenshot.save(path)
print("Settings screenshot saved")

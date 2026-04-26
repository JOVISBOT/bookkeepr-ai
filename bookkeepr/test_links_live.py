"""Test all links live in Chrome"""
import pyautogui
import time

# Test Transactions
print("Clicking Transactions...")
pyautogui.click(170, 270)
time.sleep(4)
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\test_link_1.png"
screenshot.save(path)

# Go back to Dashboard
pyautogui.click(170, 230)
time.sleep(3)

# Test Accounts
print("Clicking Accounts...")
pyautogui.click(170, 310)
time.sleep(4)
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\test_link_2.png"
screenshot.save(path)

# Go back
pyautogui.click(170, 230)
time.sleep(3)

# Test Reports
print("Clicking Reports...")
pyautogui.click(170, 350)
time.sleep(4)
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\test_link_3.png"
screenshot.save(path)

# Go back
pyautogui.click(170, 230)
time.sleep(3)

# Test Settings
print("Clicking Settings...")
pyautogui.click(170, 390)
time.sleep(4)
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\test_link_4.png"
screenshot.save(path)

print("All screenshots saved!")

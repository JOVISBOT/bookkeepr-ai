"""Test clicking Transactions link"""
import pyautogui
import time

# Close any popup
pyautogui.click(1200, 100)
time.sleep(1)

# Click on Transactions link (adjust coordinates based on sidebar)
pyautogui.click(170, 270)
time.sleep(4)

screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\clicked_transactions.png"
screenshot.save(path)
print("Transactions clicked screenshot saved")

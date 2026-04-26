"""Click on Transactions link"""
import pyautogui
import time

# Click on Transactions
pyautogui.click(200, 250)
time.sleep(3)

screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\chrome_transactions.png"
screenshot.save(path)
print("Transactions screenshot saved")

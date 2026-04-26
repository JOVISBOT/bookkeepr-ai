"""Click Delete data"""
import pyautogui
import time

# Click Delete data
pyautogui.click(1180, 780)
time.sleep(3)

# Now click on Transactions
pyautogui.click(170, 270)
time.sleep(4)

screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\after_delete_click.png"
screenshot.save(path)
print("Screenshot saved")

"""Click on Transactions"""
import pyautogui
import time

# Close restore popup first
pyautogui.keyDown('esc')
pyautogui.keyUp('esc')
time.sleep(0.5)

# Click on Transactions link
pyautogui.click(170, 270)
time.sleep(4)

# Screenshot
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\trans_clicked.png")
print("Transactions clicked screenshot saved")

"""Debug click location"""
import pyautogui
import time

# Close popup
pyautogui.keyDown('esc')
pyautogui.keyUp('esc')
time.sleep(0.5)

# Move to Transactions location and show where we're clicking
pyautogui.moveTo(170, 270)
time.sleep(2)

# Click
pyautogui.click(170, 270)
time.sleep(4)

# Now type the URL directly
pyautogui.click(600, 60)
time.sleep(0.5)
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

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\debug_result.png")
print("Debug screenshot saved")

"""Force clear cache and reload"""
import pyautogui
import time

# Open Chrome settings to clear cache
pyautogui.keyDown('ctrl')
pyautogui.keyDown('shift')
pyautogui.keyDown('delete')
pyautogui.keyUp('delete')
pyautogui.keyUp('shift')
pyautogui.keyUp('ctrl')

time.sleep(2)

# Select "All time"
pyautogui.click(1000, 400)
time.sleep(1)
pyautogui.click(1000, 600)  # All time option
time.sleep(1)

# Click Delete data
pyautogui.click(1000, 800)
time.sleep(3)

# Now navigate to transactions
pyautogui.click(500, 60)
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

# Screenshot
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\after_full_clear.png"
screenshot.save(path)
print("Screenshot saved")

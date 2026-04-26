"""Check if Chart.js is loaded"""
import pyautogui
import time

# Click console input
pyautogui.click(1150, 900)
time.sleep(1)

# Type command
pyautogui.typewrite("""typeof Chart""", interval=0.01)
time.sleep(0.5)
pyautogui.keyDown('return')
pyautogui.keyUp('return')
time.sleep(1)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\chartjs_check.png")
print("Chart.js check screenshot saved")

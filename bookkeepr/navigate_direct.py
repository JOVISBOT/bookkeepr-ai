"""Navigate directly to transactions"""
import pyautogui
import time

# Click URL bar and navigate directly
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
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\direct_trans.png")
print("Direct transactions screenshot saved")

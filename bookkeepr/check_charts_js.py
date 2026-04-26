"""Check if charts exist via JavaScript"""
import pyautogui
import time

# Open console
pyautogui.keyDown('f12')
pyautogui.keyUp('f12')
time.sleep(2)

# Click console
pyautogui.click(1150, 850)
time.sleep(1)

# Type command to check if canvas exists
pyautogui.typewrite("""document.getElementById('pnlChart')""", interval=0.01)
time.sleep(0.5)
pyautogui.keyDown('return')
pyautogui.keyUp('return')
time.sleep(1)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\js_check.png")
print("JS check screenshot saved")

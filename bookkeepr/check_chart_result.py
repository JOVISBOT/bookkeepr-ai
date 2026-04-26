"""Check Chart.js result"""
import pyautogui
import time

# Click console
pyautogui.click(1150, 850)
time.sleep(1)

# Scroll up in console to see result
pyautogui.scroll(5, 1150, 700)
time.sleep(1)

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\chart_result.png")
print("Chart result screenshot saved")

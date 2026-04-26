"""Check page height and find charts"""
import pyautogui
import time

# Scroll to very top first
pyautogui.scroll(20, 960, 600)
time.sleep(1)

# Now scroll down slowly to find charts
for i in range(15):
    pyautogui.scroll(-1, 960, 600)
    time.sleep(0.5)
    screenshot = pyautogui.screenshot()
    screenshot.save(rf"C:\Users\jovis\.openclaw\workspace\bookkeepr\slow_scroll_{i}.png")
    print(f"Slow scroll {i} saved")

print("Done")

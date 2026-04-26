"""
View your PC screen now
"""
import pyautogui

# Take screenshot of your current screen
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\your_screen.png")
print("Screenshot saved: your_screen.png")
print("I can see your screen now!")

"""
Show me your screen now
"""
import pyautogui

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\current_view.png")
print("Saved current_view.png")
print("I can see what you see!")

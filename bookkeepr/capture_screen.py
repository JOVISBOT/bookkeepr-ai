"""
Capture your screen
"""
import pyautogui

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\jo_screen.png")
print("Screen captured!")

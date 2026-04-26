"""Quick show"""
import pyautogui

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\current_screen.png")
print("Saved")

"""Quick capture"""
import pyautogui

screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\screen_now.png")
print("Screenshot saved")

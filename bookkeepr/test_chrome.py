"""Test Chrome is showing BookKeepr"""
import pyautogui
import time

time.sleep(3)
screenshot = pyautogui.screenshot()
path = r"C:\Users\jovis\.openclaw\workspace\bookkeepr\chrome_test.png"
screenshot.save(path)
print("Screenshot saved")

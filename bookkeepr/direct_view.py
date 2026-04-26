"""Direct screen capture and control"""
import pyautogui

# See your screen
screenshot = pyautogui.screenshot()
screenshot.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\screen_view.png")
print("Screen captured - I can see your desktop!")

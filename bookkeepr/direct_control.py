"""Direct control"""
import pyautogui
import subprocess
import time

# Take screenshot to see current state
screen = pyautogui.screenshot()
screen.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\see_now.png")

# Click Chrome icon on taskbar (usually at bottom)
pyautogui.click(900, 1050)
time.sleep(2)

# Screenshot after
screen = pyautogui.screenshot()
screen.save(r"C:\Users\jovis\.openclaw\workspace\bookkeepr\after_click.png")
print("Clicked Chrome on taskbar")

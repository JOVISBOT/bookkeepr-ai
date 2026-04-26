"""Check current URL"""
import pyautogui
import time

# Click on URL bar
pyautogui.click(500, 60)
time.sleep(1)

# Select all
pyautogui.keyDown('ctrl')
pyautogui.keyDown('a')
pyautogui.keyUp('a')
pyautogui.keyUp('ctrl')
time.sleep(0.5)

# Copy
pyautogui.keyDown('ctrl')
pyautogui.keyDown('c')
pyautogui.keyUp('c')
pyautogui.keyUp('ctrl')
time.sleep(0.5)

print("URL copied to clipboard")

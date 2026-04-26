"""Open Chrome to localhost"""
import subprocess
import time

# Open Chrome
subprocess.Popen([
    'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
    '--new-window',
    'http://localhost:5000/'
], shell=False)

time.sleep(5)
print("Chrome opened")

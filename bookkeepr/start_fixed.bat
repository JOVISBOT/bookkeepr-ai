@echo off
echo Setting up Python PATH...
set PATH=%PATH%;C:\Users\jovis\AppData\Local\Python\pythoncore-3.14-64\Scripts
echo.
echo Starting BookKeepr...
cd C:\Users\jovis\.openclaw\workspace\bookkeepr
C:\Users\jovis\AppData\Local\Python\pythoncore-3.14-64\python.exe run.py
pause

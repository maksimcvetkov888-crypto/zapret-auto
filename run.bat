@echo off
chcp 65001 >nul
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -NoProfile -Command "Start-Process cmd -ArgumentList '/c cd /d \"%~dp0\" && python zapret_auto.py' -Verb RunAs"
    exit
)

title ZAPRET-AUTO
cd /d "%~dp0"
python zapret_auto.py
if %errorlevel% neq 0 (
    pause
)

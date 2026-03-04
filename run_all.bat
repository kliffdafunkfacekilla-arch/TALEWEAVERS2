@echo off
echo ========================================
echo T.A.L.E.W.E.A.V.E.R. Launcher Hub
echo ========================================

:: Check for Administrator privileges (optional, but helpful for clearing strict port locks)
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Requesting Administrative Privileges for Port Clearance...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

:: Launch the secure PowerShell orchestration script
echo [+] Passing execution to secure PowerShell orchestrator...
powershell.exe -ExecutionPolicy Bypass -File "%~dp0launch_taleweavers.ps1"

pause

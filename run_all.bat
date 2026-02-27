@echo off
echo ========================================
echo T.A.L.E.W.E.A.V.E.R. Launcher
echo ========================================

echo [+] Ensuring frontend dependencies are installed...
cd saga_vtt_client
call npm install
cd ..

echo [+] Launching Master Service Runner...
python start_servers.py

pause

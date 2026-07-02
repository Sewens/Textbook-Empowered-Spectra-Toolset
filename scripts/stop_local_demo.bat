@echo off
setlocal
for %%P in (5174 5175 8001) do call :kill_port %%P
exit /b 0

:kill_port
set "PORT=%~1"
for /f "tokens=5" %%A in ('netstat -ano -p TCP ^| findstr /R /C:":%PORT% .*LISTENING"') do (
  echo Stopping port %PORT%, PID %%A
  taskkill /PID %%A /F >nul 2>nul
)
exit /b 0

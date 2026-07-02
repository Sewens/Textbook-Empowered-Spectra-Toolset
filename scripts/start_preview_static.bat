@echo off
setlocal
set "ROOT=%~dp0.."
set "PREVIEW=%ROOT%\od-prototype\preview"
set "PY=C:\Users\lawbda\scoop\apps\python313\current\python.exe"

if not exist "%PREVIEW%\index.html" (
  echo Preview index not found: %PREVIEW%\index.html
  exit /b 1
)

curl -sS --max-time 2 http://127.0.0.1:5175/index.html >nul 2>nul
if errorlevel 1 (
  start "Spectra OpenDesign Preview 5175" cmd /k "cd /d "%PREVIEW%" && "%PY%" -m http.server 5175 --bind 127.0.0.1"
) else (
  echo Preview already responding on http://127.0.0.1:5175/index.html
)

timeout /t 2 >nul
start "" http://127.0.0.1:5175/index.html
endlocal

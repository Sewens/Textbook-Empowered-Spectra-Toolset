@echo off
setlocal
set "ROOT=%~dp0.."
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"
set "UV=C:\Users\lawbda\scoop\shims\uv.exe"
set "NPM=C:\Users\lawbda\scoop\apps\nvm\current\nodejs\nodejs\npm.cmd"

if not exist "%BACKEND%\pyproject.toml" (
  echo Backend project not found: %BACKEND%
  exit /b 1
)
if not exist "%FRONTEND%\package.json" (
  echo Frontend project not found: %FRONTEND%
  exit /b 1
)

where curl >nul 2>nul
if errorlevel 1 (
  echo curl.exe is required on PATH.
  exit /b 1
)

REM Avoid inherited Hermes/Python environment leaking into the project venv.
set PYTHONPATH=
set VIRTUAL_ENV=

curl -sS --max-time 2 http://127.0.0.1:8001/health >nul 2>nul
if errorlevel 1 (
  start "Spectra Backend 8001" cmd /k "cd /d "%BACKEND%" && set PYTHONPATH=&& set VIRTUAL_ENV=&& "%UV%" run uvicorn app.main:app --host 127.0.0.1 --port 8001"
) else (
  echo Backend already responding on http://127.0.0.1:8001
)

curl -sS --max-time 2 http://127.0.0.1:5174/ >nul 2>nul
if errorlevel 1 (
  if not exist "%FRONTEND%\node_modules" (
    echo Installing frontend dependencies...
    pushd "%FRONTEND%" && "%NPM%" install && popd
  )
  start "Spectra Frontend 5174" cmd /k "cd /d "%FRONTEND%" && "%NPM%" run dev -- --port 5174"
) else (
  echo Frontend already responding on http://127.0.0.1:5174
)

echo.
echo Waiting for services...
for /l %%i in (1,1,30) do (
  curl -sS --max-time 2 http://127.0.0.1:8001/health >nul 2>nul && curl -sS --max-time 2 http://127.0.0.1:5174/ >nul 2>nul && goto ready
  timeout /t 1 >nul
)

echo Services did not become ready within 30 seconds. Check the opened terminal windows.
exit /b 1

:ready
echo Backend:  http://127.0.0.1:8001/health
echo Frontend: http://127.0.0.1:5174/
echo.
start "" http://127.0.0.1:5174/
endlocal

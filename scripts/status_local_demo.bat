@echo off
setlocal
echo === Port listeners ===
netstat -ano -p TCP | findstr /R /C:":8001 .*LISTENING" /C:":5174 .*LISTENING" /C:":5175 .*LISTENING" || echo No demo listeners found.
echo.
echo === HTTP probes ===
call :probe backend  http://127.0.0.1:8001/health
call :probe frontend http://127.0.0.1:5174/
call :probe preview  http://127.0.0.1:5175/index.html
exit /b 0

:probe
set "NAME=%~1"
set "URL=%~2"
for /f %%S in ('curl -sS -o nul -w "%%{http_code}" --max-time 5 "%URL%" 2^>nul') do set "CODE=%%S"
if "%CODE%"=="" set "CODE=DOWN"
if "%CODE%"=="000" set "CODE=DOWN"
echo %NAME% %URL% %CODE%
set "CODE="
exit /b 0

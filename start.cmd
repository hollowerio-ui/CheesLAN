@echo off
setlocal
cd /d "%~dp0"
if exist "%~dp0ChessLAN.exe" (
    start "" "%~dp0ChessLAN.exe"
    exit /b
)
set "CHESS_PY=C:\Users\LIlCr\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
if exist "%CHESS_PY%" (
    start "" "%CHESS_PY%" "%~dp0chess.py"
    exit /b
)
py -3 "%~dp0chess.py"
if errorlevel 1 pause

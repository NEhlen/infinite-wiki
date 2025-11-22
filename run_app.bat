@echo off
echo Infinite Wiki Launcher
echo ======================

REM Check if uv is installed
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo uv is not installed. Installing uv...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    
    REM Refresh environment variables for the current session
    set "PATH=%USERPROFILE%\.cargo\bin;%PATH%"
)

echo.
echo Installing/Updating dependencies...
call uv sync

echo.
echo Starting Infinite Wiki...
echo Access the app at http://127.0.0.1:8000
echo Press Ctrl+C to stop.
echo.

call uv run uvicorn app.main:app --reload

if %errorlevel% neq 0 (
    echo.
    echo Application exited with error code %errorlevel%.
    pause
)

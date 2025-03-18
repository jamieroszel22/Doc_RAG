@echo off
REM DocRAG - Streamlit App Launcher for Windows
REM This script starts the Streamlit app for DocRAG

echo Starting DocRAG Streamlit App...

REM Stop any existing Streamlit processes
echo Stopping any existing Streamlit processes...
taskkill /F /IM "streamlit.exe" /T 2>NUL
timeout /T 1 /NOBREAK >NUL

REM Start the Streamlit app
echo Starting Streamlit app at http://localhost:8501

REM Set the Streamlit server port
set STREAMLIT_SERVER_PORT=8501

REM Check if Python is available
where python >NUL 2>NUL
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
) else (
    echo Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Run the Streamlit app
%PYTHON_CMD% -m streamlit run app.py

echo DocRAG app stopped. Press any key to exit.
pause >NUL

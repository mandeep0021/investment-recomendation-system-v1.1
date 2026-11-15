@echo off
setlocal
cd /d "%~dp0"

py -3 -c "import streamlit, pandas, numpy, plotly, requests" >nul 2>nul
if errorlevel 1 (
    echo Installing project dependencies...
    py -3 -m pip install -r Requirements1.txt
    if errorlevel 1 (
        echo Dependency installation failed. Review the error above.
        pause
        exit /b 1
    )
)

py -3 -m streamlit run App1.py --server.address 127.0.0.1 --server.port 8501
if errorlevel 1 (
    echo The dashboard stopped with an error. Review the message above.
    pause
    exit /b 1
)

@echo off
rem Double-click this file to start LaabhMitra.
rem It opens two black windows (the API and the web app) and then your browser.
rem To stop the app, close the two black windows.
cd /d "%~dp0"
start "LaabhMitra API" cmd /k "backend\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --port 8000"
start "LaabhMitra Web" cmd /k "npm --prefix frontend run dev"
echo Starting LaabhMitra, please wait...
timeout /t 8 /nobreak >nul
start "" http://localhost:5173

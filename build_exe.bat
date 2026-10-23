@echo off
cd /d "%~dp0"

echo Stopping running TaskbarLyrics (if any)...
taskkill /f /im TaskbarLyrics.exe >nul 2>&1
timeout /t 2 /nobreak >nul

set PY=python
py -3.12 --version >nul 2>&1
if %errorlevel%==0 set PY=py -3.12
echo Using Python:
%PY% --version

if exist .venv rmdir /s /q .venv
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist dist (
  echo.
  echo Could not delete the dist folder. Another program is using it.
  echo Close any Explorer window showing the dist folder, then run this again.
  goto error
)

echo [1/4] Creating virtual environment...
%PY% -m venv .venv
if errorlevel 1 goto error
call .venv\Scripts\activate.bat

echo [2/4] Installing libraries...
python -m pip install --upgrade pip
if errorlevel 1 goto error
pip install winsdk requests PySide6 pyinstaller
if errorlevel 1 goto error

echo [3/4] Building EXE...
pyinstaller --noconfirm --clean --onefile --noconsole --name TaskbarLyrics --collect-all winsdk --hidden-import tblyrics.player taskbar_lyrics.py
if errorlevel 1 goto error

echo [4/4] Done!
echo dist\TaskbarLyrics.exe was created.
pause
exit /b 0

:error
echo.
echo BUILD FAILED. Please read the error messages above.
pause
exit /b 1

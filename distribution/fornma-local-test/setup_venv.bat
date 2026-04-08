@echo off
setlocal

set "ROOT_DIR=%~dp0"

python -m venv "%ROOT_DIR%.venv"
if errorlevel 1 goto :error

"%ROOT_DIR%.venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto :error

"%ROOT_DIR%.venv\Scripts\pip.exe" install -r "%ROOT_DIR%requirements-local-ui.txt"
if errorlevel 1 goto :error

echo.
echo Setup complete.
echo Run start_fornma.bat to start forNMA.
goto :eof

:error
echo Failed to create the local environment.
exit /b 1

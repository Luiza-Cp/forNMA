@echo off
setlocal

set "ROOT_DIR=%~dp0"

python -m venv "%ROOT_DIR%.venv"
if errorlevel 1 goto :error

rem Force the official PyPI index: some networks (e.g. university mirrors) point
rem pip at an incomplete mirror where common packages (pillow, napari-TRACE) are
rem missing, which breaks setup with "No matching distribution found".
set "PIP_INDEX=--index-url https://pypi.org/simple/"

"%ROOT_DIR%.venv\Scripts\python.exe" -m pip install %PIP_INDEX% --upgrade pip
if errorlevel 1 goto :error

"%ROOT_DIR%.venv\Scripts\pip.exe" install %PIP_INDEX% -r "%ROOT_DIR%requirements-local-ui.txt"
if errorlevel 1 goto :error

echo.
echo Setup complete.
echo Run start_fornma.bat to start forNMA.
goto :eof

:error
echo Failed to create the local environment.
exit /b 1

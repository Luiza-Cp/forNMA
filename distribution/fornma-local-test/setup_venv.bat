@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "VENV_PYTHON=%ROOT_DIR%.venv\Scripts\python.exe"

python -m venv "%ROOT_DIR%.venv"
if errorlevel 1 goto :error

echo Using virtual environment:
echo   %VENV_PYTHON%
echo.

"%VENV_PYTHON%" -m pip install --upgrade pip
if errorlevel 1 goto :error

"%VENV_PYTHON%" -m pip install -r "%ROOT_DIR%requirements-local-ui.txt"
if errorlevel 1 goto :error

"%VENV_PYTHON%" -c "import fastapi, uvicorn, plotly, multipart"
if errorlevel 1 goto :error

echo.
echo Setup complete.
echo Run start_fornma.bat to start forNMA.
goto :eof

:error
echo Failed to create the local environment.
echo If setup previously said packages were satisfied, delete the .venv folder in this package and run setup_venv.bat again.
exit /b 1

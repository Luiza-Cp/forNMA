@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "PYTHON_BIN=%ROOT_DIR%.venv\Scripts\python.exe"

if not exist "%PYTHON_BIN%" (
  echo Could not find the local virtual environment.
  echo Run setup_venv.bat from this same folder before starting forNMA.
  exit /b 1
)

"%PYTHON_BIN%" -c "import fastapi, uvicorn, plotly, multipart"
if errorlevel 1 (
  echo The local virtual environment is missing required packages.
  echo Run setup_venv.bat again from this same folder.
  echo If setup says everything is already satisfied, delete the .venv folder and run setup_venv.bat again.
  exit /b 1
)

echo Starting forNMA with:
echo   %PYTHON_BIN%
echo.

"%PYTHON_BIN%" "%ROOT_DIR%launcher\start_fornma.py"
endlocal

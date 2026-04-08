@echo off
setlocal

set "ROOT_DIR=%~dp0"

if exist "%ROOT_DIR%.venv\Scripts\python.exe" (
  set "PYTHON_BIN=%ROOT_DIR%.venv\Scripts\python.exe"
) else (
  set "PYTHON_BIN=python"
)

"%PYTHON_BIN%" "%ROOT_DIR%launcher\start_fornma.py"
endlocal

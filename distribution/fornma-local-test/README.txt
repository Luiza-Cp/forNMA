forNMA local test package
=========================

This package is intended for internal testing on a local PC.

What is inside
- Python source code for the backend
- Prebuilt frontend in frontend/dist
- Scripts to create a local virtual environment
- Scripts to start the backend and the frontend locally

Recommended test flow

Windows
1. Extract the zip to a normal folder, for example Desktop\fornma-local-test
2. Double-click setup_venv.bat
3. After setup finishes, double-click start_fornma.bat

Linux
1. Extract the zip
2. Run: chmod +x setup_venv.sh start_fornma.sh
3. Run: ./setup_venv.sh
4. Run: ./start_fornma.sh

What the launcher does
- Starts the API at http://127.0.0.1:8000
- Starts a local static frontend server at http://127.0.0.1:4173
- Opens the browser automatically

Important notes
- Python 3.10 to 3.12 is recommended
- First-time setup installs dependencies from the internet
- Keep the launcher terminal open while using the app
- File and folder pickers use the local operating system dialogs

If the browser does not open automatically
- Open: http://127.0.0.1:4173

If setup fails
- Confirm Python is installed and available in PATH
- Try running the setup script from a terminal to read the error message

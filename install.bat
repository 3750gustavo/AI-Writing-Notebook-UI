@echo off
set VIRTUAL_ENV_DIR=%~dp0\.venv
if not exist "%VIRTUAL_ENV_DIR%" (
    python -m venv "%VIRTUAL_ENV_DIR%"
)
call "%VIRTUAL_ENV_DIR%\Scripts\activate"
pip install -r requirements.txt
echo Environment setup complete. You can now run the application using 'start.bat'.
pause
@echo off
set VIRTUAL_ENV_DIR=%~dp0\.venv
if not exist "%VIRTUAL_ENV_DIR%\Scripts\activate" (
    call install.bat
)
call "%VIRTUAL_ENV_DIR%\Scripts\activate"
python main.py
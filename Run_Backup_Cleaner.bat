@echo off
REM Attempt to set the active code page to UTF-8 (65001) for better support of international characters.
chcp 65001 > nul

REM --- Automatic Backup File Cleaner Script Launcher ---

echo Starting the "Automatic Backup File Cleaner" tool...
REM Ensure the Python interpreter is installed and in the system's PATH environment variable.
REM The Python script (backup_file_remover.py) will attempt to automatically install its required dependencies.

python backup_file_remover.py

echo.
echo Script execution finished. You can check the log file on your Desktop.
REM The "pause" command below will keep this window open after the script finishes, until the user presses any key.
pause

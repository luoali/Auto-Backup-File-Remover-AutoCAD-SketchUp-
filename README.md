# Auto Backup File Remover (AutoCAD & SketchUp)

## Description

This Python script automatically finds and helps you remove redundant backup files created by AutoCAD (`.bak`) and SketchUp (`.skb`) from your computer. It intelligently targets only those backup files for which the original drawing (`.dwg`) or model (`.skp`) file still exists in the same directory. To ensure safety, files are moved to the system's Recycle Bin (Trash) rather than being permanently deleted.

This script is designed for users who want to free up disk space by removing unnecessary backup files without manually searching for them.

## Features

* **Comprehensive Scanning**: Scans all accessible local disk drives on your computer.
* **Specific Targeting**: Identifies AutoCAD (`.bak`) and SketchUp (`.skb`) backup files.
* **Original File Verification**: Critically verifies the existence of the corresponding original file (`.dwg` or `.skp`) before flagging a backup for removal.
* **Automatic Dependency Management**: On its first run (or if dependencies are missing), the script checks for and attempts to automatically install required Python libraries (`psutil`, `send2trash`, `tqdm`) using `pip`.
* **User-Friendly Progress**: Displays clear progress bars using `tqdm` for:
    * Scanning each disk drive, showing the iteration rate and current directory being scanned.
    * The file deletion process, showing progress as files are moved to the Recycle Bin.
* **Safe Deletion**: Moves files to the system's Recycle Bin/Trash, allowing for recovery if needed.
* **Unified Confirmation (Default Mode)**:
    1.  Scans all drives and collects a list of all eligible backup files.
    2.  Presents this complete list to you.
    3.  Asks for a single "yes/no" confirmation before moving *all* listed files to the Recycle Bin.
* **No-Confirm Mode (Optional)**: The script can be easily configured (by editing one line) to run without any confirmation prompts, automatically moving all found eligible files to the Recycle Bin. This is useful for automated tasks or if you are confident in the script's operation.
* **Detailed Logging**: Records all operations, including drives scanned, files found, files moved, files skipped, and any errors encountered, into a timestamped log file saved on your Desktop (e.g., `YYYYMMDD_HHMMSS_backup_file_remover.log`).
* **Smart Directory Exclusion**: Automatically excludes common system directories (like Program Files, Windows in Windows OS), the user's AppData folder, and Recycle Bin folders themselves to prevent accidental damage, improve scanning speed, and avoid irrelevant results.

## Requirements

* **Python**: Python 3.x (Python 3.6 or newer recommended).
* **pip**: Python's package installer, which usually comes with Python.
* **Required Python Libraries**:
    * `psutil` (for accessing disk partition and system information)
    * `send2trash` (for sending files safely to the Recycle Bin/Trash)
    * `tqdm` (for displaying progress bars)
    * _Note: The script will attempt to install these automatically if they are not found._

## Setup

1.  **Ensure Python 3 is installed**: If not, download and install it from [python.org](https://www.python.org/downloads/). Make sure to check the option "Add Python to PATH" during installation (Windows).
2.  **Download the Script**: Save the `backup_file_remover.py` file to a directory on your computer.
3.  **Dependencies**: No manual installation of the Python libraries is typically needed. The script is designed to handle this for you on its first run. If automatic installation fails due to permission issues, you might need to install them manually (see "Important Notes").

## Usage

1.  **Open your Terminal/Command Prompt**:
    * Windows: Search for `cmd` or `PowerShell`.
    * macOS/Linux: Open `Terminal`.
2.  **Navigate to the script's directory**: Use the `cd` command. For example, if you saved it in `F:\Python\backup_file_remover`:
    ```bash
    cd F:\Python\backup_file_remover
    ```
3.  **Run the script**:
    ```bash
    python backup_file_remover.py
    ```
4.  **First Run**: If required libraries are missing, the script will attempt to install them. You'll see messages related to this.
5.  **Scanning**: The script will then begin scanning your drives. You'll see progress bars for each drive, indicating the directory currently being scanned. This can take some time depending on your hard drive size and number of files.
6.  **Review and Confirm (Default Mode)**: After scanning all drives, if eligible backup files are found, they will be listed in the terminal. The script will then ask for a single confirmation:
    ```
    是否将以上 X 个文件全部移动到回收站？ (y/n):
    ```
    Type `y` and press Enter to proceed, or `n` and press Enter to cancel.
7.  **Completion**: After the operation (or cancellation), a summary message will be displayed.
8.  **Check Logs**: A detailed log file will be created on your Desktop with a name like `YYYYMMDD_HHMMSS_backup_file_remover.log`.

## No-Confirm Mode

If you want the script to automatically move all found eligible files to the Recycle Bin without asking for confirmation each time:

1.  Open the `backup_file_remover.py` script in a text editor.
2.  Scroll towards the end of the file until you find the `if __name__ == "__main__":` block.
3.  Locate this line:
    ```python
    delete_backup_files(confirm=True)
    ```
4.  Change `True` to `False`:
    ```python
    delete_backup_files(confirm=False)
    ```
5.  Save the script. Now, when you run it, it will skip the final confirmation step.

## How It Works (Briefly)

1.  **Initialization**: Sets up logging to a file on the Desktop.
2.  **Dependency Check**: Verifies and installs `psutil`, `send2trash`, and `tqdm` if missing.
3.  **Disk Discovery**: Uses `psutil` to get a list of all readable disk partitions.
4.  **Exclusion List**: Defines system and user-specific directories (like AppData, Program Files, Windows, Recycle Bins) to be excluded from the scan.
5.  **Iterative Scanning**:
    * For each disk drive, it uses `os.walk()` to traverse its directory structure.
    * A `tqdm` progress bar visualizes the scanning progress for the current drive, also showing the directory being processed.
    * It skips any directory that falls under the predefined exclusion list.
6.  **File Identification**: Within each directory, it looks for files with `.bak` (AutoCAD) or `.skb` (SketchUp) extensions.
7.  **Original File Verification**: If a backup file is found, the script checks if the corresponding original file (e.g., `drawing.dwg` for `drawing.bak`) exists in the same directory.
8.  **Candidate Collection**: If the original file exists, the backup file is added to a list of "candidates for deletion."
9.  **Summary and Confirmation**: After scanning all drives:
    * If no candidates were found, it informs the user.
    * Otherwise, it prints a list of all candidate backup files.
    * If `confirm=True` (default), it prompts the user for a single confirmation to delete all listed files.
10. **Moving to Recycle Bin**: If confirmed (or if `confirm=False`), the script iterates through the candidate list:
    * Each file is moved to the system's Recycle Bin using `send2trash`.
    * A `tqdm` progress bar shows the progress of this operation.
    * Success or failure for each file move is logged.
11. **Final Logging**: A summary of the operation (number of files moved/failed) is logged and printed.

## Important Notes

* **Use with Caution**: Although this script moves files to the Recycle Bin (allowing for recovery) and not permanently deleting them, it's always wise to be careful. Review the list of files presented by the script before confirming deletion, especially during initial runs.
* **Permissions**:
    * The script needs read access to the directories it scans. If it encounters protected directories it cannot access, it will log a warning and skip them.
    * Moving files to the Recycle Bin requires appropriate write/delete permissions for those files.
    * If the automatic installation of Python packages (`pip install ...`) fails, it might be due to insufficient permissions. In such cases, you might need to run your terminal/command prompt with **administrator privileges** (Windows) or use `sudo` (macOS/Linux) to manually install the packages:
        ```bash
        pip install psutil send2trash tqdm
        ```
* **Scanning Time**: Please be patient. Scanning entire hard drives, especially large ones or those with a vast number of files, can take a considerable amount of time (minutes to hours). The progress bars are there to provide feedback during this process.
* **Log Files**: The log file created on your Desktop is your best friend for understanding exactly what the script did, which files it identified, which it moved, and if any errors occurred. Always check it if you have questions or encounter issues.
* **System Variations**: Behavior related to Recycle Bin functionality can sometimes vary slightly between operating systems or even different versions of the same OS. `send2trash` aims to handle these variations gracefully.

---

This script was developed with the assistance of an AI. Always review and test scripts from any source before running them on critical data.

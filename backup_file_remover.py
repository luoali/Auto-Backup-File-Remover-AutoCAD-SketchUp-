import os
import logging
import datetime
import subprocess
import sys
import importlib.util
# tqdm will be used for progress bars. It will be imported after dependency check.

# --- Configure Paths and Logging ---
# Get Desktop path
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# Ensure Desktop path exists, try to create it or fall back if it doesn't
if not os.path.exists(desktop_path):
    print(f"Warning: Desktop path {desktop_path} does not exist.")
    try:
        os.makedirs(desktop_path, exist_ok=True)
        print(f"Attempted to create desktop directory: {desktop_path}")
    except OSError as e:
        print(f"Could not create desktop directory {desktop_path} ({e}). Log will be saved in the current working directory.")
        desktop_path = os.getcwd() # Fall back to current working directory for logs

log_file_name = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") + "_backup_file_remover.log"
log_file_path = os.path.join(desktop_path, log_file_name)

# Configure logging
# filemode='w' overwrites the log file on each run, 'a' appends.
logging.basicConfig(filename=log_file_path, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filemode='w')

# --- Dependency Check and Installation Function ---
def check_and_install_packages(packages):
    """
    Checks if specified Python packages are installed and attempts to install them using pip if not.
    Args:
        packages (list): A list of package names to check and install.
    Returns:
        bool: True if all packages are installed or successfully installed, False otherwise.
    """
    all_successful = True
    for package in packages:
        spec = importlib.util.find_spec(package)
        if spec is None:
            print(f"Module {package} not installed. Attempting to install...")
            logging.info(f"Module {package} not installed. Attempting to install...")
            try:
                # Use sys.executable to ensure pip is called for the current Python interpreter
                process = subprocess.Popen(
                    [sys.executable, "-m", "pip", "install", package],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True, # Process output as text
                    errors='ignore' # Ignore decoding errors
                )
                stdout, stderr = process.communicate()

                if process.returncode == 0:
                    print(f"Module {package} installed successfully.")
                    logging.info(f"Module {package} installed successfully.")
                else:
                    error_message = f"Failed to install module {package}. Return code: {process.returncode}\nPip Stdout: {stdout}\nPip Stderr: {stderr}"
                    print(error_message)
                    logging.error(error_message)
                    all_successful = False
            except FileNotFoundError:
                error_message = f"Error: pip command not found (tried via {sys.executable} -m pip). Please ensure pip is installed and configured for your current Python environment."
                print(error_message)
                logging.error(error_message)
                all_successful = False
            except Exception as e:
                error_message = f"An unknown error occurred while installing module {package}: {e}"
                print(error_message)
                logging.error(error_message)
                all_successful = False
        else:
            # print(f"Module {package} is already installed.") # Can be uncommented to show this info
            logging.info(f"Module {package} is already installed.")
    return all_successful

# --- Main Script Logic ---
# Add tqdm to the list of required packages
required_packages = ["psutil", "send2trash", "tqdm"]
print("Checking required modules...")
dependencies_ok = check_and_install_packages(required_packages)

if not dependencies_ok:
    message = "One or more required modules could not be installed. The script may not run correctly or will exit now."
    print(message)
    logging.critical(message)
    sys.exit("Dependency installation failed. Exiting script. Please check the log for details or try installing required modules manually.")

# After dependency check, import the modules
try:
    import psutil
    import send2trash
    from tqdm import tqdm # Import tqdm after ensuring it's installed
except ImportError as e:
    critical_message = f"Error importing required modules even after attempting installation: {e}.\nPlease check the log and ensure modules are correctly installed for Python environment '{sys.executable}'.\nScript will exit."
    print(critical_message)
    logging.critical(critical_message)
    sys.exit(critical_message)

def delete_backup_files(confirm=True):
    """
    Automatically finds AutoCAD and SketchUp backup files.
    If confirm=True, it will ask for a single confirmation after scanning to delete all found files.
    If confirm=False, it will automatically delete all found files.
    """
    search_dirs = []
    try:
        for partition in psutil.disk_partitions():
            # Include only read-write physical drives, excluding special devices like CD-ROMs
            # Also check if the mountpoint is indeed a directory
            if 'rw' in partition.opts.lower() and os.path.isdir(partition.mountpoint):
                search_dirs.append(partition.mountpoint)
            else:
                logging.info(f"Skipping non-read-write or non-directory mountpoint: {partition.mountpoint} (opts: {partition.opts})")
    except Exception as e:
        print(f"Failed to get disk partition information: {e}")
        logging.error(f"Failed to get disk partition information: {e}")
        return 
    
    if not search_dirs:
        print("No scannable disk drives found.")
        logging.warning("No scannable disk drives found. Script will exit.")
        return

    # Define base directories for exclusion
    exclude_dirs_definitions = [
        os.path.join(os.path.expanduser("~"), "AppData"), # User AppData
    ]
    # For system-level directories like Program Files, Windows, get them this way (Windows example):
    if os.name == 'nt': # If Windows OS
        program_files = os.environ.get('ProgramFiles')
        program_files_x86 = os.environ.get('ProgramFiles(x86)')
        windows_dir = os.environ.get('WINDIR')
        # Ensure these environment variable paths actually exist and are directories
        if program_files and os.path.isdir(program_files): 
            exclude_dirs_definitions.append(program_files)
        if program_files_x86 and os.path.isdir(program_files_x86): 
            exclude_dirs_definitions.append(program_files_x86)
        if windows_dir and os.path.isdir(windows_dir): 
            exclude_dirs_definitions.append(windows_dir)
        
        # Exclude Recycle Bins ($Recycle.Bin) from the root of all scanned drives
        for part_path in search_dirs: 
             common_recycle_bin = os.path.join(part_path, '$Recycle.Bin') 
             if os.path.isdir(common_recycle_bin):
                 exclude_dirs_definitions.append(common_recycle_bin)
    
    # Convert to normalized absolute paths and keep only existing directories for efficiency
    exclude_dirs = []
    for p_def in exclude_dirs_definitions:
        if p_def and os.path.isdir(p_def): # Re-confirm path is not None and is a directory
            exclude_dirs.append(os.path.normpath(os.path.abspath(p_def)))
        elif p_def: # p_def exists but is not a directory (e.g., user defined an invalid path or env var returned non-dir)
            logging.warning(f"Defined exclusion path '{p_def}' is not a valid directory and will be ignored.")
            
    if exclude_dirs:
        logging.info(f"The following confirmed existing directories and their subdirectories will be excluded: {exclude_dirs}")
    else:
        logging.info("No valid exclusion directories configured or found.")

    files_to_delete_candidates = [] # List to store files pending deletion

    print("\nStarting scan for backup files, please wait...") # Overall start message
    for search_dir in search_dirs:
        # Print clear start message for each drive
        print(f"\n===== Starting scan of drive: {search_dir} =====")
        logging.info(f"Starting scan of drive: {search_dir}")

        walk_iterator = os.walk(search_dir, topdown=True, onerror=lambda err: logging.warning(f"Cannot access item in directory '{err.filename}': {err.strerror}"))
        
        drive_label = search_dir.replace('\\','').replace(':','') # Try to get drive letter, e.g., C, D
        if not drive_label: drive_label = os.path.basename(search_dir.rstrip(os.sep)) # Fallback to last part of path
        if not drive_label: drive_label = search_dir # Worst case

        with tqdm(walk_iterator, desc=f"Scanning {drive_label}", unit=" dirs", leave=False, dynamic_ncols=True, ascii=True) as pbar:
            for dirpath, dirnames, filenames in pbar:
                display_path = dirpath
                if len(display_path) > 60: # Shorten long paths for display
                    display_path = "..." + display_path[-57:]
                pbar.set_postfix_str(f"Current: {display_path}", refresh=True)

                current_normalized_dirpath = os.path.normpath(os.path.abspath(dirpath))
                is_excluded = False
                if exclude_dirs: # Only check if there are exclusion rules
                    for excluded_path in exclude_dirs:
                        if current_normalized_dirpath.startswith(excluded_path):
                            is_excluded = True
                            break # Found a matching exclusion rule, no need to check others
                if is_excluded:
                    dirnames[:] = []  # Clear subdirectories list, stop os.walk from going deeper here
                    continue          # Skip current excluded directory, continue to next item in os.walk

                for filename in filenames:
                    if filename.endswith((".bak", ".skb")):
                        backup_file = os.path.join(current_normalized_dirpath, filename)
                        base_name, ext = os.path.splitext(backup_file)
                        original_file = ""
                        if ext == ".bak": original_file = base_name + ".dwg"
                        elif ext == ".skb": original_file = base_name + ".skp"
                        else: 
                            # This case should ideally not happen due to endswith filter above
                            logging.warning(f"Found unknown backup file extension '{ext}' for file: {backup_file}")
                            continue 

                        if os.path.exists(original_file):
                            logging.info(f"Candidate for deletion: Found backup file '{backup_file}' (original file '{original_file}' exists).")
                            files_to_delete_candidates.append(backup_file)
    
    sys.stderr.write("\n") # Ensure newline after tqdm for clean subsequent printing
    print("Scanning of all drives completed.")
    
    # --- Scan complete, process uniformly ---
    if not files_to_delete_candidates:
        print("No eligible backup files found.")
        logging.info("Scan complete. No eligible backup files found.")
        return

    print(f"\nFound {len(files_to_delete_candidates)} eligible backup file(s):")
    for i, f_path in enumerate(files_to_delete_candidates, 1):
        print(f"  {i}. {f_path}")
    
    proceed_with_deletion = False
    if confirm:
        try:
            user_response = input(f"\nMove all {len(files_to_delete_candidates)} listed file(s) to Recycle Bin? (y/n): ").strip().lower()
            if user_response == 'y':
                proceed_with_deletion = True
            else:
                print("Operation cancelled by user. No files were moved.")
                logging.info(f"User chose not to move {len(files_to_delete_candidates)} candidate file(s).")
        except KeyboardInterrupt: # User pressed Ctrl+C
            print("\nOperation interrupted by user (Ctrl+C). No files were moved.")
            logging.warning("Operation interrupted by user via KeyboardInterrupt.")
            return 
        except EOFError: # User might have sent EOF via Ctrl+Z (Windows) or Ctrl+D (Unix)
            print("\nInput stream ended, operation cancelled. No files were moved.")
            logging.warning("User ended input stream (EOFError), operation cancelled.")
            return
    else: # confirm is False
        print("\nconfirm=False, will automatically move all found files to Recycle Bin.")
        logging.info(f"confirm=False, automatically processing {len(files_to_delete_candidates)} candidate file(s).")
        proceed_with_deletion = True

    if proceed_with_deletion:
        deleted_count = 0
        failed_count = 0
        print("\nMoving files to Recycle Bin...")
        # Also add a progress bar for the deletion process
        with tqdm(files_to_delete_candidates, desc="Moving files", unit=" file(s)", dynamic_ncols=True, ascii=True) as delete_pbar:
            for backup_file_to_delete in delete_pbar:
                delete_pbar.set_postfix_str(os.path.basename(backup_file_to_delete), refresh=True)
                try:
                    send2trash.send2trash(backup_file_to_delete)
                    logging.info(f"Moved to Recycle Bin: {backup_file_to_delete}")
                    deleted_count += 1
                except Exception as e: # send2trash might raise various exceptions, e.g., send2trash.TrashPermissionError
                    # Print errors clearly below the tqdm progress bar
                    sys.stderr.write(f"\n  Failed to move file '{backup_file_to_delete}': {e}\n")
                    logging.error(f"Failed to move file '{backup_file_to_delete}' to Recycle Bin: {e}")
                    failed_count += 1
        
        summary_message = f"Operation complete. Successfully moved {deleted_count} file(s), failed to move {failed_count} file(s)."
        print(f"\n{summary_message}")
        logging.info(summary_message)

# --- Script Entry Point ---
if __name__ == "__main__":
    # Ensure all print messages are visible in the console when run directly
    # (tqdm prints to stderr by default, normal print to stdout, usually fine)
    try:
        print("Starting Backup File Remover script...")
        logging.info("Script execution started.")
        delete_backup_files(confirm=True) # Default is to confirm once after scan
        print(f"\nScript execution finished. Log file saved to: {log_file_path}")
        logging.info("Script execution finished.")
    except Exception as e:
        # Catch any unexpected top-level errors, log and print
        print(f"An unexpected error occurred during script execution: {e}")
        logging.critical(f"An unexpected error occurred during script execution: {e}", exc_info=True)

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import time
import shutil
from pathlib import Path
import threading
from paths import prod_book_names_path, prod_book_loaners_path, prod_loans_log_path, backup_dir_path

def backup_files():
    """Backup all CSV files to the backup directory with timestamp"""
    while True:
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = backup_dir / timestamp
            backup_path.mkdir(exist_ok=True)
            
            # Backup all CSV files
            for file in [prod_book_names_path, prod_book_loaners_path, prod_loans_log_path]:
                if os.path.exists(file):
                    shutil.copy2(file, backup_path / Path(file).name)
            
            # Keep only last 24 backups (4 hours worth of backups)
            backups = sorted(backup_dir.glob('*'), key=os.path.getctime)
            if len(backups) > 24:
                for old_backup in backups[:-24]:
                    shutil.rmtree(old_backup)
                    
        except Exception as e:
            print(f"Backup error: {e}")
            
        time.sleep(600)  # Sleep for 10 minutes

def init_backup():
    global backup_dir
    # Create backup directory if it doesn't exist
    backup_dir = Path(backup_dir_path)
    backup_dir.mkdir(exist_ok=True) # Create backup directory if it doesn't exist

    # Start backup thread
    backup_thread = threading.Thread(target=backup_files, daemon=True)
    backup_thread.start()

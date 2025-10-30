"""
Backup and Restore Utilities for RAG System
Handles creating and restoring backup archives
"""

import os
import zipfile
import shutil
from datetime import datetime
from pathlib import Path

BACKUP_DIR = os.path.join(os.path.dirname(__file__), "Backups")
os.makedirs(BACKUP_DIR, exist_ok=True)

def create_backup(exclude_patterns=None):
    """
    Create a backup zip of the RAG System directory
    
    Args:
        exclude_patterns: List of patterns to exclude (e.g., ['Web_Imports', '.chromadb'])
        
    Returns:
        Path to backup zip file, or None if failed
    """
    if exclude_patterns is None:
        exclude_patterns = ['Web_Imports', '__pycache__', '.pyc', 'node_modules', '.git']
    
    rag_system_path = os.path.dirname(__file__)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"RAG_Backup_{timestamp}.zip"
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Walk through all files
            for root, dirs, files in os.walk(rag_system_path):
                # Filter out excluded directories
                dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
                
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Skip excluded patterns
                    if any(pattern in file_path for pattern in exclude_patterns):
                        continue
                    
                    # Skip the backup file itself and backup directory
                    if 'Backups' in file_path and file.endswith('.zip'):
                        continue
                    
                    # Calculate relative path
                    arcname = os.path.relpath(file_path, rag_system_path)
                    
                    # Add to zip
                    zipf.write(file_path, arcname)
                    print(f"Added: {arcname}")
        
        # Get file size
        size_mb = os.path.getsize(backup_path) / (1024 * 1024)
        
        return backup_path, size_mb
    
    except Exception as e:
        print(f"Backup failed: {e}")
        return None, 0

def list_backups():
    """List all available backups"""
    backups = []
    if not os.path.exists(BACKUP_DIR):
        return backups
    
    for file in os.listdir(BACKUP_DIR):
        if file.endswith('.zip') and file.startswith('RAG_Backup_'):
            file_path = os.path.join(BACKUP_DIR, file)
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            timestamp_str = file.replace('RAG_Backup_', '').replace('.zip', '')
            
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                backups.append({
                    'filename': file,
                    'path': file_path,
                    'size_mb': size_mb,
                    'timestamp': timestamp
                })
            except:
                backups.append({
                    'filename': file,
                    'path': file_path,
                    'size_mb': size_mb,
                    'timestamp': None
                })
    
    # Sort by timestamp (newest first)
    backups.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min, reverse=True)
    return backups

def restore_backup(backup_path, target_dir=None):
    """
    Restore from a backup zip file
    
    Args:
        backup_path: Path to backup zip file
        target_dir: Directory to restore to (default: RAG_System directory)
        
    Returns:
        True if successful, False otherwise
    """
    if target_dir is None:
        target_dir = os.path.dirname(__file__)
    
    if not os.path.exists(backup_path):
        print(f"Backup file not found: {backup_path}")
        return False
    
    try:
        # Create restore directory
        restore_dir = os.path.join(target_dir, "restore_temp")
        if os.path.exists(restore_dir):
            shutil.rmtree(restore_dir)
        os.makedirs(restore_dir)
        
        # Extract backup
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            zipf.extractall(restore_dir)
        
        print(f"Backup extracted to: {restore_dir}")
        print("Review files in restore_temp, then manually restore needed files")
        print("This is a safety feature - review before overwriting!")
        
        return True
    
    except Exception as e:
        print(f"Restore failed: {e}")
        return False

def restore_backup_full(backup_path, target_dir=None, confirm=False):
    """
    Full restore - overwrites target directory (use with caution!)
    
    Args:
        backup_path: Path to backup zip file
        target_dir: Directory to restore to
        confirm: Must be True to proceed
        
    Returns:
        True if successful
    """
    if not confirm:
        print("Restore confirmation required!")
        return False
    
    if target_dir is None:
        target_dir = os.path.dirname(__file__)
    
    try:
        # Extract directly to target
        with zipfile.ZipFile(backup_path, 'r') as zipf:
            # Get base directory from backup
            members = zipf.namelist()
            if not members:
                print("Backup is empty!")
                return False
            
            # Extract all files
            zipf.extractall(target_dir)
        
        print(f"Restore complete to: {target_dir}")
        return True
    
    except Exception as e:
        print(f"Restore failed: {e}")
        return False

if __name__ == "__main__":
    # Test backup
    print("Creating backup...")
    backup_path, size = create_backup()
    if backup_path:
        print(f"Backup created: {backup_path} ({size:.2f} MB)")
    
    # List backups
    print("\nAvailable backups:")
    for backup in list_backups():
        print(f"  {backup['filename']} - {backup['size_mb']:.2f} MB")





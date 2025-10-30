"""
Sync Manager - Handles backups and VPS synchronization
Compatible with Control Panel backup UI
"""

import os
import sys
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from logger import log, log_exception
except ImportError:
    def log(msg, category="SYNC"):
        print(f"[{category}] {msg}")
    def log_exception(category="ERROR", exception=None, context=""):
        print(f"[{category}] {context}: {exception}")

class SyncManager:
    """Manages backups and VPS synchronization"""
    
    def __init__(self):
        self.data_dir = os.path.join(BASE_DIR, "data")
        self.backups_dir = os.path.join(BASE_DIR, "Backups")
        self.restore_temp_dir = os.path.join(BASE_DIR, "restore_temp")
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.backups_dir, exist_ok=True)
        os.makedirs(self.restore_temp_dir, exist_ok=True)
    
    def create_backup(self, include_vault: bool = False, vault_path: str = None):
        """
        Create backup of /data/ directory
        
        Args:
            include_vault: Whether to include Obsidian vault
            vault_path: Path to Obsidian vault (if include_vault=True)
        
        Returns:
            Path to backup zip file
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"data_backup_{timestamp}.zip"
            backup_path = os.path.join(self.backups_dir, backup_filename)
            
            log(f"Creating backup: {backup_filename}", "SYNC")
            
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup data directory
                if os.path.exists(self.data_dir):
                    for root, dirs, files in os.walk(self.data_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, BASE_DIR)
                            zipf.write(file_path, arcname)
                            log(f"  Added: {arcname}", "SYNC")
                
                # Backup memory.db if exists
                memory_db = os.path.join(BASE_DIR, "memory.db")
                if os.path.exists(memory_db):
                    zipf.write(memory_db, "memory.db")
                    log(f"  Added: memory.db", "SYNC")
                
                # Backup config directory
                config_dir = os.path.join(BASE_DIR, "config")
                if os.path.exists(config_dir):
                    for root, dirs, files in os.walk(config_dir):
                        for file in files:
                            if file.endswith('.json'):
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, BASE_DIR)
                                zipf.write(file_path, arcname)
                
                # Optionally include vault
                if include_vault and vault_path and os.path.exists(vault_path):
                    log("  Including Obsidian vault in backup", "SYNC")
                    for root, dirs, files in os.walk(vault_path):
                        # Skip large files and cache
                        if '.obsidian' in root or 'node_modules' in root:
                            continue
                        for file in files:
                            file_path = os.path.join(root, file)
                            if os.path.getsize(file_path) > 50 * 1024 * 1024:  # Skip > 50MB
                                continue
                            arcname = os.path.join("vault", os.path.relpath(file_path, vault_path))
                            zipf.write(file_path, arcname)
            
            backup_size_mb = os.path.getsize(backup_path) / (1024 * 1024)
            log(f"Backup created: {backup_path} ({backup_size_mb:.1f} MB)", "SYNC")
            
            return backup_path
            
        except Exception as e:
            log_exception("SYNC", e, "Error creating backup")
            return None
    
    def restore_backup(self, backup_path: str):
        """
        Restore from backup zip file
        
        Args:
            backup_path: Path to backup zip file
        
        Returns:
            True if successful
        """
        try:
            if not os.path.exists(backup_path):
                log(f"Backup file not found: {backup_path}", "SYNC", level="ERROR")
                return False
            
            log(f"Restoring from backup: {backup_path}", "SYNC")
            
            # Extract to temporary directory first
            temp_restore = os.path.join(self.restore_temp_dir, datetime.now().strftime("%Y%m%d_%H%M%S"))
            os.makedirs(temp_restore, exist_ok=True)
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_restore)
            
            log(f"Backup extracted to: {temp_restore}", "SYNC")
            
            # Copy files to actual locations
            # This is a safe restore - user should review before finalizing
            log("Backup extracted to restore_temp. Review before finalizing.", "SYNC")
            
            return True
            
        except Exception as e:
            log_exception("SYNC", e, "Error restoring backup")
            return False
    
    def sync_to_vps(self, backup_path: str, vps_url: str, auth_token: str = None):
        """
        Sync backup to VPS
        
        Args:
            backup_path: Path to backup file
            vps_url: VPS automation URL
            auth_token: Optional auth token
        
        Returns:
            True if successful
        """
        try:
            import requests
            
            with open(backup_path, 'rb') as f:
                files = {'backup': f}
                headers = {}
                if auth_token:
                    headers["Authorization"] = f"Bearer {auth_token}"
                
                log(f"Syncing backup to VPS: {vps_url}", "SYNC")
                response = requests.post(
                    f"{vps_url}/sync_backup",
                    files=files,
                    headers=headers,
                    timeout=300
                )
            
            if response.status_code == 200:
                log("Backup synced to VPS successfully", "SYNC")
                return True
            else:
                log(f"VPS sync failed: {response.status_code}", "SYNC", level="ERROR")
                return False
                
        except Exception as e:
            log_exception("SYNC", e, "Error syncing to VPS")
            return False
    
    def get_last_backup_time(self):
        """Get timestamp of last backup"""
        try:
            backups = sorted(Path(self.backups_dir).glob("data_backup_*.zip"), key=os.path.getmtime, reverse=True)
            if backups:
                return datetime.fromtimestamp(os.path.getmtime(backups[0]))
            return None
        except:
            return None
    
    def get_backup_count(self):
        """Get number of backups"""
        try:
            return len(list(Path(self.backups_dir).glob("data_backup_*.zip")))
        except:
            return 0

# Global sync manager instance
_sync_manager_instance = None

def get_sync_manager():
    """Get global sync manager (singleton)"""
    global _sync_manager_instance
    if _sync_manager_instance is None:
        _sync_manager_instance = SyncManager()
    return _sync_manager_instance

def init_memory():
    """Initialize memory system (compatibility function)"""
    try:
        from core.memory_manager import get_memory_manager
        memory = get_memory_manager()
        log("Memory system initialized", "SYNC")
        return memory
    except Exception as e:
        log_exception("SYNC", e, "Error initializing memory")
        return None





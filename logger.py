"""
Unified logging system for RAG Academic Assistant
Provides structured, rotating logs with categories
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Logs")
MAX_LOG_SIZE_MB = 5
MAX_LOG_SIZE_BYTES = MAX_LOG_SIZE_MB * 1024 * 1024

# Ensure log directory exists
os.makedirs(LOG_DIR, exist_ok=True)

def _get_log_file():
    """Get today's log file path"""
    today = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(LOG_DIR, f"{today}.log")

def _rotate_logs():
    """Compress or delete old logs if they exceed size limit"""
    try:
        log_file = _get_log_file()
        
        # Compress logs older than 7 days
        for old_log in Path(LOG_DIR).glob("*.log"):
            if old_log.name == os.path.basename(log_file):
                continue  # Skip current log
            
            age_days = (datetime.now() - datetime.fromtimestamp(old_log.stat().st_mtime)).days
            if age_days > 7:
                try:
                    # Compress with gzip
                    import gzip
                    compressed_name = str(old_log) + ".gz"
                    with open(old_log, 'rb') as f_in:
                        with gzip.open(compressed_name, 'wb') as f_out:
                            f_out.writelines(f_in)
                    os.remove(old_log)
                    log(f"Compressed old log: {old_log.name}", "LOGGER", print_to_console=False)
                except Exception as e:
                    # If compression fails, try to delete
                    try:
                        if age_days > 30:  # Delete if > 30 days
                            os.remove(old_log)
                    except:
                        pass
        
        # Clean up compressed logs > 7 days
        for compressed_log in Path(LOG_DIR).glob("*.log.gz"):
            age_days = (datetime.now() - datetime.fromtimestamp(compressed_log.stat().st_mtime)).days
            if age_days > 7:
                try:
                    os.remove(compressed_log)
                except:
                    pass
        
        # Handle current log file size
        if os.path.exists(log_file) and os.path.getsize(log_file) > MAX_LOG_SIZE_BYTES:
            # Compress old log by renaming with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            compressed_name = log_file.replace(".log", f"_{timestamp}.log.bak")
            
            # Compress with gzip
            try:
                import gzip
                with open(log_file, 'rb') as f_in:
                    with gzip.open(compressed_name + ".gz", 'wb') as f_out:
                        f_out.writelines(f_in)
                os.remove(log_file)
            except:
                # Fallback to rename
                os.rename(log_file, compressed_name)
            
    except Exception as e:
        # Don't fail if log rotation fails
        pass

def log(message, category="INFO", print_to_console=True):
    """
    Unified logging function
    
    Args:
        message: Log message
        category: Category tag (API, INDEX, GUI, LLM, etc.)
        print_to_console: Whether to print to stdout (default: True)
    """
    try:
        _rotate_logs()
        
        log_file = _get_log_file()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{category}] {message}\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
        
        if print_to_console:
            print(f"[{category}] {message}", flush=True)
            
    except Exception as e:
        # Fallback if logging fails
        try:
            print(f"[LOG_ERROR] Failed to write log: {e}", file=sys.stderr)
        except:
            pass

def log_exception(category="ERROR", exception=None, context=""):
    """Log an exception with traceback"""
    import traceback
    try:
        exc_type = type(exception).__name__ if exception else "Exception"
        exc_msg = str(exception) if exception else "Unknown error"
        tb = traceback.format_exc()
        
        error_msg = f"{context} | {exc_type}: {exc_msg}\n{tb}" if context else f"{exc_type}: {exc_msg}\n{tb}"
        log(error_msg, category, print_to_console=False)
        
        # Print summary to console
        print(f"[{category}] {context}: {exc_type}: {exc_msg}", file=sys.stderr)
    except:
        pass

def get_recent_logs(lines=50, category=None):
    """Get recent log entries (for GUI display)"""
    try:
        log_file = _get_log_file()
        if not os.path.exists(log_file):
            return []
        
        with open(log_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        
        recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
        
        if category:
            recent = [line for line in recent if f"[{category}]" in line]
        
        return recent
    except:
        return []


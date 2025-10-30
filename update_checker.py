"""
Update Checker for RAG System
Checks for newer versions from GitHub or local repo
"""

import os
import json
import subprocess
from datetime import datetime

VERSION_FILE = os.path.join(os.path.dirname(__file__), ".version")
CURRENT_VERSION = "v1.2.0-Julian-Polish"

def get_current_version():
    """Get current version"""
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r') as f:
                data = json.load(f)
                return data.get('version', CURRENT_VERSION)
        except:
            pass
    return CURRENT_VERSION

def save_version(version):
    """Save version to file"""
    data = {
        'version': version,
        'date': datetime.now().isoformat()
    }
    with open(VERSION_FILE, 'w') as f:
        json.dump(data, f)

def check_github_updates(repo_url=None):
    """
    Check for updates on GitHub
    
    Args:
        repo_url: GitHub repository URL (optional)
        
    Returns:
        (has_update, latest_version, message)
    """
    # For now, return no update (local repo)
    # Can be extended to check GitHub releases
    return False, CURRENT_VERSION, "Local repository - no remote check"

def check_local_git_updates():
    """
    Check for updates in local git repository
    
    Returns:
        (has_update, latest_version, message)
    """
    try:
        # Check if git is available
        result = subprocess.run(
            ["git", "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return False, CURRENT_VERSION, "Git not available"
        
        # Check if we're in a git repo
        result = subprocess.run(
            ["git", "status"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
            timeout=5
        )
        
        if result.returncode != 0:
            return False, CURRENT_VERSION, "Not a git repository"
        
        # Get latest commit
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H %s"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__),
            timeout=5
        )
        
        if result.returncode == 0:
            commit_info = result.stdout.strip()
            return False, CURRENT_VERSION, f"Local git repo: {commit_info[:50]}"
        
    except FileNotFoundError:
        return False, CURRENT_VERSION, "Git not installed"
    except Exception as e:
        return False, CURRENT_VERSION, f"Error checking git: {e}"
    
    return False, CURRENT_VERSION, "No updates available"

def check_for_updates():
    """
    Check for updates (tries multiple methods)
    
    Returns:
        (has_update, latest_version, update_message)
    """
    current = get_current_version()
    
    # Try local git first
    has_update, latest_version, message = check_local_git_updates()
    
    # If local git doesn't show updates, try GitHub
    if not has_update:
        has_update, latest_version, message = check_github_updates()
    
    return has_update, latest_version, message

if __name__ == "__main__":
    print(f"Current version: {get_current_version()}")
    has_update, version, message = check_for_updates()
    print(f"Update available: {has_update}")
    print(f"Message: {message}")


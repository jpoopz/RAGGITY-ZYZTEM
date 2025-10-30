"""
Config Encryption Utility
Encrypts sensitive config data at rest using Fernet
"""

import os
import sys
import json
import base64

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

try:
    from cryptography.fernet import Fernet
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    print("WARNING: cryptography not available, config encryption disabled")

class ConfigEncryptor:
    """Encrypts/decrypts sensitive config values"""
    
    def __init__(self, key_path=None):
        if key_path is None:
            key_path = os.path.join(BASE_DIR, "remote", "keys", "config.key")
        
        self.key_path = key_path
        self.key = None
        self._load_or_generate_key()
    
    def _load_or_generate_key(self):
        """Load or generate encryption key"""
        if not ENCRYPTION_AVAILABLE:
            return
        
        try:
            if os.path.exists(self.key_path):
                with open(self.key_path, 'rb') as f:
                    self.key = f.read()
            else:
                self.key = Fernet.generate_key()
                os.makedirs(os.path.dirname(self.key_path), exist_ok=True)
                with open(self.key_path, 'wb') as f:
                    f.write(self.key)
        except Exception as e:
            print(f"Error loading/generating config key: {e}")
    
    def encrypt_value(self, value: str) -> str:
        """Encrypt a string value"""
        if not ENCRYPTION_AVAILABLE or not self.key:
            return value  # Return plaintext if encryption unavailable
        
        try:
            fernet = Fernet(self.key)
            encrypted = fernet.encrypt(value.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            print(f"Encryption error: {e}")
            return value
    
    def decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt an encrypted string value"""
        if not ENCRYPTION_AVAILABLE or not self.key:
            return encrypted_value  # Assume plaintext if decryption unavailable
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_value.encode('utf-8'))
            fernet = Fernet(self.key)
            return fernet.decrypt(encrypted_bytes).decode('utf-8')
        except:
            # If decryption fails, assume it's plaintext
            return encrypted_value
    
    def encrypt_config(self, config: dict, sensitive_keys: list = None) -> dict:
        """Encrypt sensitive keys in config dict"""
        if sensitive_keys is None:
            sensitive_keys = ['api_token', 'auth_token', 'password', 'secret']
        
        encrypted_config = config.copy()
        
        for key in sensitive_keys:
            if key in encrypted_config and isinstance(encrypted_config[key], str):
                if not encrypted_config[key].startswith('ENCRYPTED:'):
                    encrypted_config[key] = f"ENCRYPTED:{self.encrypt_value(encrypted_config[key])}"
        
        return encrypted_config
    
    def decrypt_config(self, config: dict, sensitive_keys: list = None) -> dict:
        """Decrypt sensitive keys in config dict"""
        if sensitive_keys is None:
            sensitive_keys = ['api_token', 'auth_token', 'password', 'secret']
        
        decrypted_config = config.copy()
        
        for key in sensitive_keys:
            if key in decrypted_config and isinstance(decrypted_config[key], str):
                if decrypted_config[key].startswith('ENCRYPTED:'):
                    encrypted_value = decrypted_config[key].replace('ENCRYPTED:', '', 1)
                    decrypted_config[key] = self.decrypt_value(encrypted_value)
        
        return decrypted_config

# Global encryptor instance
_config_encryptor = None

def get_config_encryptor():
    """Get global config encryptor"""
    global _config_encryptor
    if _config_encryptor is None:
        _config_encryptor = ConfigEncryptor()
    return _config_encryptor





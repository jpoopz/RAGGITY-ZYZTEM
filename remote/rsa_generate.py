"""
RSA Key Generation Script
Generates RSA key pair for Cloud Bridge encryption
"""

import os
import sys

# Force UTF-8
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

try:
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
except ImportError:
    print("ERROR: cryptography package required")
    print("Install with: pip install cryptography")
    sys.exit(1)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYS_DIR = os.path.join(BASE_DIR, "remote", "keys")

def generate_rsa_keypair():
    """Generate RSA 2048-bit key pair"""
    print("Generating RSA 2048-bit key pair...")
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Ensure keys directory exists
    os.makedirs(KEYS_DIR, exist_ok=True)
    
    # Save private key
    private_path = os.path.join(KEYS_DIR, "private.pem")
    with open(private_path, 'wb') as f:
        f.write(private_pem)
    print(f"✅ Private key saved: {private_path}")
    print(f"   ⚠️  KEEP THIS SECRET! Do not share or commit to git.")
    
    # Save public key
    public_path = os.path.join(KEYS_DIR, "public.pem")
    with open(public_path, 'wb') as f:
        f.write(public_pem)
    print(f"✅ Public key saved: {public_path}")
    print(f"   → Copy this to VPS: ~/assistant/keys/public.pem")
    
    # Save public key for VPS (instructions)
    print("\n" + "="*60)
    print("📋 Next Steps:")
    print("="*60)
    print("1. Copy public.pem to your VPS:")
    print(f"   scp {public_path} user@your-vps-ip:~/assistant/keys/public.pem")
    print("\n2. Ensure private.pem stays local (never upload)")
    print("\n3. Configure VPS_AUTH_TOKEN in environment:")
    print("   export VPS_AUTH_TOKEN='your-secure-random-token'")
    print("\n4. Update config/vps_config.json with:")
    print("   - vps_url: https://your-vps-domain")
    print("   - api_token: (same as VPS_AUTH_TOKEN)")
    print("="*60)
    
    return private_path, public_path

if __name__ == "__main__":
    if os.path.exists(os.path.join(KEYS_DIR, "private.pem")):
        response = input("RSA keys already exist. Regenerate? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled.")
            sys.exit(0)
    
    generate_rsa_keypair()





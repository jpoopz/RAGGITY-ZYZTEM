# Encryption Overview - RSA/AES Flow Diagram

**Version:** 4.0.0  
**Last Updated:** 2025-10-29

---

## 🔐 **ENCRYPTION ARCHITECTURE**

### Overview

The Cloud Bridge uses a **hybrid encryption scheme**:

1. **RSA 2048-bit** for key exchange (optional)
2. **AES-256 (Fernet)** for payload encryption (primary)
3. **Token Authentication** for API security

---

## 📊 **FLOW DIAGRAM**

```
┌─────────────────────────────────────────────────────────────────┐
│                      LOCAL CLIENT                                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 1. Initialize
                              ▼
                    ┌─────────────────────┐
                    │ Load RSA Keys       │
                    │ - private.pem       │
                    │ - public.pem        │
                    └──────────┬──────────┘
                               │
                               │ 2. Generate/Load AES Key
                               ▼
                    ┌─────────────────────┐
                    │ AES Key (Fernet)     │
                    │ - auto-generated     │
                    │ - stored in aes.key │
                    └──────────┬──────────┘
                               │
                               │ 3. Build Payload
                               ▼
                    ┌─────────────────────┐
                    │ Context Bundle       │
                    │ {memory, rag, ...}   │
                    └──────────┬──────────┘
                               │
                               │ 4. Encrypt (if enabled)
                               ▼
                    ┌─────────────────────┐
                    │ Encrypted Payload    │
                    │ AES(Fernet)          │
                    └──────────┬──────────┘
                               │
                               │ 5. Add Auth Header
                               ▼
                    ┌─────────────────────┐
                    │ HTTP Request         │
                    │ Authorization:       │
                    │   Bearer <token>     │
                    │ Body: Encrypted      │
                    └──────────┬──────────┘
                               │
                               │ 6. HTTPS/TLS
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      VPS SERVER                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ 7. Verify Token
                              ▼
                    ┌─────────────────────┐
                    │ Validate Auth Token  │
                    └──────────┬──────────┘
                               │
                               │ 8. Decrypt Payload
                               ▼
                    ┌─────────────────────┐
                    │ Load AES Key         │
                    │ (same as client)    │
                    └──────────┬──────────┘
                               │
                               │ 9. Decrypt
                               ▼
                    ┌─────────────────────┐
                    │ Decrypted Context    │
                    │ {memory, rag, ...}   │
                    └──────────┬──────────┘
                               │
                               │ 10. Process & Store
                               ▼
                    ┌─────────────────────┐
                    │ Store in Storage     │
                    │ context_storage/     │
                    └─────────────────────┘
```

---

## 🔑 **KEY MANAGEMENT**

### RSA Keys

**Purpose:** Optional key exchange (future: secure AES key transmission)

**Generation:**
```bash
python remote/rsa_generate.py
```

**Files:**
- `remote/keys/private.pem` - **NEVER SHARE** (local only)
- `remote/keys/public.pem` - Copy to VPS

**Usage:**
- Currently used for key handshake validation
- Future: Encrypt AES key with RSA public key

---

### AES Key (Fernet)

**Purpose:** Primary encryption for all payloads

**Generation:**
```python
from cryptography.fernet import Fernet
key = Fernet.generate_key()  # 256-bit
```

**Storage:**
- `remote/keys/aes.key` (local)
- `~/assistant/keys/aes.key` (VPS)

**Sharing:**
- Must be **synchronized** between local and VPS
- Copy manually or via secure channel
- Same key on both sides = encrypted communication

**Rotation:**
- Generate new key on both sides
- Update `aes.key` files
- Restart services

---

## 🔒 **ENCRYPTION PROCESS**

### Encrypt Payload

```python
from cryptography.fernet import Fernet

# Load key
with open("keys/aes.key", "rb") as f:
    key = f.read()

# Create Fernet instance
fernet = Fernet(key)

# Encrypt
payload = {"data": "sensitive information"}
encrypted = fernet.encrypt(
    json.dumps(payload).encode('utf-8')
)

# Result: Base64-encoded encrypted bytes
```

### Decrypt Payload

```python
# Decrypt
decrypted = fernet.decrypt(encrypted)
payload = json.loads(decrypted.decode('utf-8'))
```

---

## 🔐 **AUTHENTICATION**

### Token-Based Auth

**Local Config:**
```json
{
  "api_token": "abc123xyz..."
}
```

**VPS Environment:**
```bash
export VPS_AUTH_TOKEN="abc123xyz..."
```

**HTTP Header:**
```
Authorization: Bearer abc123xyz...
```

**Validation:**
```python
def verify_token(authorization: str):
    token = authorization.replace("Bearer ", "")
    return token == VPS_AUTH_TOKEN
```

---

## 📋 **SECURITY CHECKLIST**

### Key Security

- [ ] RSA private key: **Never uploaded to VPS**
- [ ] RSA public key: Safe to share
- [ ] AES key: Must match on both sides
- [ ] Auth token: Strong, random, secret

### Transport Security

- [ ] Use HTTPS (TLS 1.2+) in production
- [ ] Certificate from Let's Encrypt
- [ ] Validate certificate on client

### Access Control

- [ ] Firewall rules restrict port access
- [ ] Rate limiting (future)
- [ ] IP whitelist (optional)

### Monitoring

- [ ] Log authentication failures
- [ ] Monitor for suspicious activity
- [ ] Track encryption errors

---

## 🧪 **TESTING ENCRYPTION**

### Verify Keys Exist

**Local:**
```bash
ls -la remote/keys/
# Should see: private.pem, public.pem, aes.key
```

**VPS:**
```bash
ls -la ~/assistant/keys/
# Should see: public.pem, aes.key
```

### Test Encryption/Decryption

**Local:**
```python
from core.cloud_bridge import get_cloud_bridge
bridge = get_cloud_bridge()

# Test encrypt
data = {"test": "data"}
encrypted = bridge.encrypt_payload(data)
print(f"Encrypted: {len(encrypted)} bytes")

# Test decrypt
decrypted = bridge.decrypt_payload(encrypted)
print(f"Decrypted: {decrypted}")
```

**VPS:**
```python
# Similar test in cloud_bridge_server.py
```

### Test End-to-End

1. Enable encryption in config
2. Sync context from local
3. Check VPS logs: Should decrypt successfully
4. Pull context back
5. Verify data integrity

---

## ⚠️ **IMPORTANT NOTES**

1. **AES Key Must Match:**
   - Both local and VPS must have the **same** `aes.key`
   - If keys differ, decryption will fail

2. **RSA Keys Are Optional:**
   - Currently used for validation only
   - Can operate without RSA (AES-only)

3. **Token Security:**
   - Use strong, random tokens
   - Rotate periodically
   - Never commit to git

4. **HTTPS is Recommended:**
   - Even with encryption, use HTTPS in production
   - Protects against man-in-the-middle
   - Let's Encrypt provides free certificates

---

## 🔄 **KEY ROTATION PROCEDURE**

### Rotate AES Key

1. **Generate new key on both sides:**
   ```python
   from cryptography.fernet import Fernet
   new_key = Fernet.generate_key()
   ```

2. **Update files:**
   - Local: `remote/keys/aes.key`
   - VPS: `~/assistant/keys/aes.key`

3. **Restart services:**
   - Local: Restart GUI/auto-sync
   - VPS: `sudo systemctl restart julian-cloud-bridge`

4. **Verify:**
   - Test sync from local
   - Check logs for errors

### Rotate Auth Token

1. **Generate new token:**
   ```bash
   openssl rand -hex 32
   ```

2. **Update configs:**
   - Local: `config/vps_config.json`
   - VPS: `~/assistant/.auth_token` or environment

3. **Restart services**

4. **Verify:**
   - Test connection
   - Check authentication logs

---

**Encryption Status:** ✅ Operational  
**Security Level:** Production-Ready (with HTTPS)





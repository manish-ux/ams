# security.py
import os
import hashlib

def hash_password(password: str) -> bytes:
    """
    Hash a plaintext password using PBKDF2-HMAC (SHA256) with a random salt.
    Returns the salt+hash as bytes.
    """
    salt = os.urandom(16)  # 16-byte salt
    hashed = hashlib.pbkdf2_hmac(
        'sha256',           # hash function
        password.encode(),  # convert the password to bytes
        salt,
        100_000             # number of iterations
    )
    # Store salt + hashed password in one field:
    return salt + hashed

def verify_password(stored_value: bytes, provided_password: str) -> bool:
    """
    Verify a provided password by extracting the salt from the stored_value
    and re-computing the hash.
    """
    salt = stored_value[:16]
    stored_hash = stored_value[16:]
    
    new_hash = hashlib.pbkdf2_hmac(
        'sha256',
        provided_password.encode(),
        salt,
        100_000
    )
    return new_hash == stored_hash

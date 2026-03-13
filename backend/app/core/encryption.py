"""Shared encryption utility using Fernet symmetric encryption.

The encryption key is derived from SECRET_KEY so no separate key management
is needed — rotating the secret key will invalidate all encrypted values.
"""
import base64
import hashlib
from cryptography.fernet import Fernet, InvalidToken
from app.core.config import settings


def _get_fernet() -> Fernet:
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_value(plaintext: str) -> str:
    """Encrypt a plaintext string. Returns a URL-safe base64 token."""
    if not plaintext:
        return plaintext
    return _get_fernet().encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """Decrypt a value produced by encrypt_value. Raises InvalidToken on failure."""
    if not ciphertext:
        return ciphertext
    return _get_fernet().decrypt(ciphertext.encode()).decode()


def mask_secret(value: str) -> str:
    """Return a masked representation showing only the last 4 characters.

    Examples:
        "sk-abc123xyz" -> "sk-****3xyz"
        "short"        -> "****ort"   (fallback for very short keys)
    """
    if not value:
        return ""
    visible = value[-4:]
    return f"****{visible}"

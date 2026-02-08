import os
import base64
import secrets
from typing import Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from loguru import logger

# Get encryption key from environment or use a default (INSECURE for production)
_APP_KEY = os.getenv("APP_SECRET_KEY")
_SALT = os.getenv("APP_KEY_SALT")
if not _SALT:
    if os.getenv("ENVIRONMENT") == "production":
        raise RuntimeError("APP_KEY_SALT must be set in production!")
    _SALT = "dev-only-salt-do-not-use-in-production"
_SALT = _SALT.encode()

# Generate random key for development (different each startup for security)
_DEV_SECRET_KEY = secrets.token_bytes(32)

def _get_fernet() -> Fernet:
    """Generate Fernet instance from APP_SECRET_KEY"""
    if not _APP_KEY:
        if os.getenv("ENVIRONMENT") == "production":
            raise RuntimeError("APP_SECRET_KEY must be set in production environment!")
        logger.warning("APP_SECRET_KEY not set! Using random key for development (will change on restart).")
        key_material = _DEV_SECRET_KEY
    else:
        key_material = _APP_KEY.encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(key_material))
    return Fernet(key)

def encrypt_sensitive(data: str) -> str:
    """Encrypt sensitive string"""
    if not data:
        return data
    try:
        f = _get_fernet()
        return f.encrypt(data.encode()).decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise

def decrypt_sensitive(encrypted_data: str) -> str:
    """Decrypt sensitive string"""
    if not encrypted_data:
        return encrypted_data
    try:
        f = _get_fernet()
        return f.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        # If decryption fails, raise exception
        raise

class Sanitizer:
    """Sensitive information sanitizer"""

    SENSITIVE_PATTERNS = [
        r'(password|secret|token|key|pwd|auth)[\"\']?\s*[:=]\s*[\"\']?([^\s\"\'\,]+)',
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',  # Email
        r'(ghp_[a-zA-Z0-9]+)',  # GitHub Token
        r'(sk-[a-zA-Z0-9]+)',   # OpenAI/DeepSeek Key
    ]

    @staticmethod
    def sanitize(message: str) -> str:
        """Sanitize sensitive information in string"""
        import re
        if not message:
            return message

        sanitized = message
        # Basic replacement for common patterns
        for pattern in Sanitizer.SENSITIVE_PATTERNS:
            try:
                # Use a callback to preserve the key but mask the value
                def replace_callback(match):
                    full_match = match.group(0)
                    if len(match.groups()) > 1:
                        # Key-Value pair (group 1 is key, group 2 is value)
                        key = match.group(1)
                        # Keep key, mask value
                        return full_match.replace(match.group(2), "***")
                    else:
                        # Single match (e.g. email or token)
                        return "***"

                sanitized = re.sub(pattern, replace_callback, sanitized, flags=re.IGNORECASE)
            except Exception:
                pass

        return sanitized

    @staticmethod
    def verify_token(token: str, secret: str, algorithm: str = "HS256") -> dict:
        """
        Verify JWT token with strict expiration check

        Args:
            token: The JWT token string
            secret: The secret key for decoding
            algorithm: The algorithm used for decoding

        Returns:
            The decoded payload

        Raises:
            Exception: If token is invalid or expired
        """
        import jwt

        # Explicitly require expiration claim and verify it
        options = {
            "verify_signature": True,
            "verify_exp": True,
            "require": ["exp", "iat"]
        }

        return jwt.decode(token, secret, algorithms=[algorithm], options=options)

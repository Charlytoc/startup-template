"""Fernet-based symmetric encryption helpers for sensitive JSON blobs (integration auth, etc.)."""

from __future__ import annotations

import json
from typing import Any

from cryptography.fernet import Fernet


def encrypt(data: str, key: str) -> str:
    """Encrypt a string using Fernet symmetric encryption."""
    fernet = Fernet(key.encode())
    return fernet.encrypt(data.encode()).decode()


def decrypt(encrypted_data: str, key: str) -> str:
    """Decrypt a Fernet-encrypted string."""
    fernet = Fernet(key.encode())
    return fernet.decrypt(encrypted_data.encode()).decode()


def encrypt_dict(data: dict[str, Any], key: str) -> str:
    """JSON-serialize a dict and Fernet-encrypt the resulting string."""
    return encrypt(json.dumps(data), key)


def decrypt_dict(encrypted_data: str, key: str) -> dict[str, Any]:
    """Inverse of :func:`encrypt_dict`."""
    return json.loads(decrypt(encrypted_data, key))

"""@File: audio2text/config/_decoder.py
@Description: XOR+Base64 decoder for v0.15 obfuscated API keys.
    Matches the old backend/config_manager.py v0.15.1 XOR logic.
@Version: 0.16.0
@Author: CENF Development Team
@License: Apache-2.0
"""

from __future__ import annotations

import base64

_XOR_KEY: str = "CENF_SECRET"


def decode_xor_key(encoded: str) -> str:
    """Decode an XOR+Base64 obfuscated API key.

    If the value already looks like a plaintext key (starts with known
    prefixes), it is returned as-is.
    """
    if not encoded:
        return ""
    # Already plaintext (starts with known prefixes)
    if encoded.startswith(("gsk_", "sk-", "nvapi-")):
        return encoded
    try:
        decoded_bytes = base64.b64decode(encoded)
        result = "".join(
            chr(b ^ ord(_XOR_KEY[i % len(_XOR_KEY)]))
            for i, b in enumerate(decoded_bytes)
        )
        if not result.startswith(("gsk_", "sk-", "nvapi-")):
            return encoded
        return result
    except Exception:
        return encoded

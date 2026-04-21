"""Shared detection of user-initiated context-reset commands (Telegram, Instagram DMs, etc.)."""

from __future__ import annotations

CLEAR_CONTEXT_REPLY = "Done. I cleared our previous context. Send your next message."


def is_clear_context_text(text: str) -> bool:
    """True when the first token is a known reset command (same semantics as Telegram private chat)."""
    t = text.strip().lower()
    if not t:
        return False
    command = t.split(maxsplit=1)[0]
    return command in {"/clear", "/clearcontext", "/reset"} or command.startswith("/clear@")

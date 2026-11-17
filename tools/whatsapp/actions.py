"""Tool-facing adapter that reuses the existing WhatsApp implementation."""

from __future__ import annotations

import time

from tools.whatapp import (
    REUSED_TAB_WAIT_SECONDS,
    WHATSAPP_LOAD_WAIT_SECONDS,
    WHATSAPP_URL,
    open_brave_tab,
    reuse_whatsapp_tab,
    search_and_send_message,
)


def send_message(contact_name: str, message: str) -> dict[str, str]:
    """Send a WhatsApp message using the existing Brave automation."""
    _ensure_whatsapp_tab()

    search_and_send_message(contact_name, message)
    return {"status": "sent", "contact_name": contact_name}


def open_whatsapp() -> dict[str, str]:
    """Open or activate WhatsApp Web in Brave without sending a message."""
    reused = _ensure_whatsapp_tab()
    return {"status": "ready", "reused_existing_tab": str(reused).lower()}


def _ensure_whatsapp_tab() -> bool:
    reused = reuse_whatsapp_tab()
    if reused:
        time.sleep(REUSED_TAB_WAIT_SECONDS)
    else:
        open_brave_tab(WHATSAPP_URL)
        time.sleep(WHATSAPP_LOAD_WAIT_SECONDS)
    return reused

#!/usr/bin/env python3
"""Open WhatsApp Web and search for a contact in the existing Brave window.

This uses macOS's ``open`` command and Accessibility keyboard events, not
Playwright or another browser automation library.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time


WHATSAPP_URL = "https://web.whatsapp.com/"
WHATSAPP_LOAD_WAIT_SECONDS = 5
REUSED_TAB_WAIT_SECONDS = 0.5
SEARCH_RESULT_WAIT_SECONDS = 0.5
CHAT_OPEN_WAIT_SECONDS = 1


def open_brave_tab(url: str) -> None:
    """Ask the running Brave Browser application to open *url* in a tab."""
    if sys.platform != "darwin":
        raise RuntimeError("This script currently supports macOS only.")

    if shutil.which("open") is None:  # pragma: no cover - always available on macOS
        raise RuntimeError("The macOS 'open' command was not found.")

    # Using the application name lets macOS forward the open request to the
    # existing Brave process instead of creating a separate browser session.
    subprocess.run(["open", "-a", "Brave Browser", url], check=True)


def reuse_whatsapp_tab() -> bool:
    """Activate an existing WhatsApp Web tab, returning whether one was found."""
    if shutil.which("osascript") is None:  # pragma: no cover - macOS only
        raise RuntimeError("The macOS 'osascript' command was not found.")

    apple_script = """
on run
    tell application "Brave Browser"
        repeat with windowIndex from 1 to (count windows)
            repeat with tabIndex from 1 to (count tabs of window windowIndex)
                set currentWindow to window windowIndex
                set currentTab to tab tabIndex of currentWindow
                if (URL of currentTab starts with "https://web.whatsapp.com/") then
                    set active tab index of currentWindow to tabIndex
                    set index of currentWindow to 1
                    activate
                    return "found"
                end if
            end repeat
        end repeat
    end tell
    return "not_found"
end run
"""
    result = subprocess.run(
        ["osascript", "-"],
        input=apple_script,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or "Unknown AppleScript error"
        raise RuntimeError(details)
    return result.stdout.strip() == "found"


def search_and_send_message(contact_name: str, message: str) -> None:
    """Search for a contact, open the first result, and send a message."""
    if shutil.which("osascript") is None:  # pragma: no cover - macOS only
        raise RuntimeError("The macOS 'osascript' command was not found.")

    # WhatsApp Web's macOS search shortcut is Command+Control+/.  Sending the
    # slash by key code is more reliable than sending it as text, especially
    # when the user's keyboard layout is not US English.
    apple_script = """
on run argv
    set contactName to item 1 of argv
    set messageText to item 2 of argv
    tell application "Brave Browser" to activate
    tell application "System Events"
        tell process "Brave Browser"
            set frontmost to true
        end tell
        delay 0.2
        key code 44 using {{command down, control down}}
        delay 0.2
        keystroke contactName
        delay {search_wait}
        key code 36
        delay {chat_wait}
        keystroke messageText
        delay 0.1
        key code 36
    end tell
end run
""".format(
        search_wait=SEARCH_RESULT_WAIT_SECONDS,
        chat_wait=CHAT_OPEN_WAIT_SECONDS,
    )
    result = subprocess.run(
        ["osascript", "-", contact_name, message],
        input=apple_script,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        details = result.stderr.strip() or "Unknown AppleScript error"
        if "not allowed assistive access" in details:
            raise RuntimeError(
                "macOS blocked keyboard control. Open System Settings > "
                "Privacy & Security > Accessibility and enable the app used "
                "to run this script (for example Terminal), then try again."
            )
        raise RuntimeError(details)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Open WhatsApp Web and search for a contact in Brave."
    )
    parser.add_argument(
        "contact_name",
        help="contact name to search for in WhatsApp",
    )
    parser.add_argument(
        "message",
        nargs="+",
        help="message to send",
    )
    args = parser.parse_args()
    message = " ".join(args.message)

    try:
        if reuse_whatsapp_tab():
            print("Reusing the existing WhatsApp tab.")
            time.sleep(REUSED_TAB_WAIT_SECONDS)
        else:
            open_brave_tab(WHATSAPP_URL)
            print(f"Waiting {WHATSAPP_LOAD_WAIT_SECONDS} seconds for WhatsApp Web...")
            time.sleep(WHATSAPP_LOAD_WAIT_SECONDS)
        search_and_send_message(args.contact_name, message)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Could not open Brave: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

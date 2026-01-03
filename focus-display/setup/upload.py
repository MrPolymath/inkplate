#!/usr/bin/env python3
"""
Focus Display - Upload Script

Uploads all necessary files to the Inkplate device.

Usage:
    python upload.py

Requirements:
    - mpremote installed (pip install mpremote)
    - Inkplate connected via USB
"""

import os
import subprocess
import sys
from pathlib import Path

# Default serial port for Inkplate (from CLAUDE.md)
DEFAULT_PORT = "/dev/cu.usbserial-110"

# Files to upload (relative to focus-display folder)
FILES_TO_UPLOAD = [
    "main.py",
    "config.py",
    "secrets.py",
    "display.py",
    "calendar_sync.py",
]

# Project root
PROJECT_DIR = Path(__file__).parent.parent


def find_device():
    """Try to find the Inkplate device."""
    # Check default port first
    if os.path.exists(DEFAULT_PORT):
        return DEFAULT_PORT

    # Try to find any USB serial device
    import glob
    ports = glob.glob("/dev/cu.usbserial-*") + glob.glob("/dev/tty.usbserial-*")

    if ports:
        return ports[0]

    return None


def check_secrets():
    """Check if secrets.py exists."""
    secrets_path = PROJECT_DIR / "secrets.py"
    if not secrets_path.exists():
        print("Error: secrets.py not found!")
        print("Run 'python setup_oauth.py' first to generate it.")
        return False
    return True


def upload_file(port, local_path, remote_name):
    """Upload a single file to the device."""
    cmd = ["mpremote", "connect", port, "cp", str(local_path), f":{remote_name}"]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  Error: {result.stderr}")
        return False
    return True


def reset_device(port):
    """Reset the device to start the new code."""
    cmd = ["mpremote", "connect", port, "reset"]
    subprocess.run(cmd, capture_output=True)


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║           Focus Display - Upload to Device                 ║
╚═══════════════════════════════════════════════════════════╝
""")

    # Check for secrets.py
    if not check_secrets():
        sys.exit(1)

    # Find device
    print("Looking for Inkplate device...")
    port = find_device()

    if not port:
        print("\nError: No Inkplate device found!")
        print("Make sure:")
        print("  1. The device is connected via USB")
        print("  2. You have the correct USB driver installed")
        print(f"\nExpected port: {DEFAULT_PORT}")
        sys.exit(1)

    print(f"Found device at: {port}")

    # Upload each file
    print("\nUploading files:")
    all_success = True

    for filename in FILES_TO_UPLOAD:
        local_path = PROJECT_DIR / filename
        if not local_path.exists():
            print(f"  {filename}: SKIP (not found)")
            continue

        print(f"  {filename}...", end=" ", flush=True)
        if upload_file(port, local_path, filename):
            print("OK")
        else:
            print("FAILED")
            all_success = False

    if not all_success:
        print("\nSome files failed to upload. Check errors above.")
        sys.exit(1)

    # Reset device
    print("\nResetting device...")
    reset_device(port)

    print("""
╔═══════════════════════════════════════════════════════════╗
║                    Upload Complete!                        ║
╠═══════════════════════════════════════════════════════════╣
║                                                            ║
║  Your Focus Display should now be running.                ║
║  It will:                                                 ║
║    1. Connect to WiFi                                     ║
║    2. Sync with Google Calendar                           ║
║    3. Show your focus time                                ║
║                                                            ║
║  The display refreshes every 5 minutes.                   ║
║                                                            ║
╚═══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()

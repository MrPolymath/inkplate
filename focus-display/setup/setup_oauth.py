#!/usr/bin/env python3
"""
Focus Display - OAuth Setup Script

This script handles Google Calendar OAuth authentication and generates
the secrets.py file for your Inkplate device.

Prerequisites:
1. Create a Google Cloud Project at https://console.cloud.google.com
2. Enable the Google Calendar API
3. Create OAuth 2.0 credentials (Desktop app type)
4. Download the credentials JSON file

Usage:
    python setup_oauth.py
"""

import os
import sys
import subprocess
import platform
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Error: Required packages not installed.")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

# OAuth scopes - read-only calendar access
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# Path to output secrets file
SECRETS_FILE = Path(__file__).parent.parent / "secrets.py"


def scan_wifi_networks():
    """Scan for available WiFi networks on macOS."""
    if platform.system() != "Darwin":
        return []

    try:
        # Use system_profiler to get WiFi networks (more reliable than deprecated airport)
        result = subprocess.run(
            ["system_profiler", "SPAirPortDataType"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return []

        # Parse output to extract network names
        networks = []
        lines = result.stdout.split("\n")
        in_networks_section = False

        # Section headers to ignore
        ignore_names = {"awdl0", "Current Network Information", "Interfaces", "Wi-Fi"}

        for line in lines:
            # Look for the networks section
            if "Other Local Wi-Fi Networks:" in line:
                in_networks_section = True
                continue

            # Stop when we hit a new major section (not indented enough)
            if in_networks_section and line and not line.startswith("            "):
                if not line.startswith("          "):
                    break

            if in_networks_section:
                # Network names are deeply indented (12 spaces) and end with ":"
                # They appear before PHY Mode, Channel, etc.
                stripped = line.strip()

                # Skip metadata lines
                if stripped.startswith(("PHY Mode", "Channel", "Network Type", "Security")):
                    continue

                # Check for network name (ends with ":" but isn't a known section)
                if stripped and stripped.endswith(":"):
                    network_name = stripped[:-1]  # Remove trailing colon
                    if network_name and network_name not in networks and network_name not in ignore_names:
                        networks.append(network_name)

        return networks
    except Exception as e:
        print(f"WiFi scan failed: {e}")
        return []


def get_wifi_credentials():
    """Prompt user for WiFi credentials with network scanning."""
    print("\n" + "=" * 50)
    print("WiFi Configuration")
    print("=" * 50)

    # Try to scan for networks
    print("\nScanning for WiFi networks...")
    networks = scan_wifi_networks()

    ssid = None

    if networks:
        print("\nAvailable networks:")
        for i, network in enumerate(networks, 1):
            print(f"  {i}. {network}")
        print(f"  {len(networks) + 1}. [Enter manually]")

        choice = input(f"\nSelect network [1-{len(networks) + 1}]: ").strip()

        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(networks):
                ssid = networks[choice_num - 1]
                print(f"Selected: {ssid}")
        except ValueError:
            pass

    if not ssid:
        ssid = input("Enter your WiFi network name (SSID): ").strip()

    password = input("Enter your WiFi password: ").strip()

    return ssid, password


def get_google_credentials():
    """
    Guide user through Google OAuth setup.
    Returns client_id, client_secret, refresh_token.
    """
    print("\n" + "=" * 50)
    print("Google Calendar OAuth Setup")
    print("=" * 50)

    print("""
To set up Google Calendar access, you need to:

1. Go to https://console.cloud.google.com
2. Create a new project (or select existing)
3. Enable the "Google Calendar API"
4. Go to "APIs & Services" > "Credentials"
5. Click "Create Credentials" > "OAuth client ID"
6. Select "Desktop app" as application type
7. Download the JSON credentials file

Do you have your credentials JSON file ready?
""")

    creds_path = input("Enter path to credentials JSON file (or press Enter to input manually): ").strip()

    if creds_path and os.path.exists(creds_path):
        # Use credentials file
        flow = InstalledAppFlow.from_client_secrets_file(creds_path, SCOPES)
        print("\nOpening browser for Google login...")
        credentials = flow.run_local_server(port=8080)

        # Extract what we need
        client_id = flow.client_config["client_id"]
        client_secret = flow.client_config["client_secret"]
        refresh_token = credentials.refresh_token

        return client_id, client_secret, refresh_token

    else:
        # Manual input
        print("\nEnter your OAuth credentials manually:")
        client_id = input("Client ID: ").strip()
        client_secret = input("Client Secret: ").strip()

        # Create flow manually
        client_config = {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        }

        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        print("\nOpening browser for Google login...")
        credentials = flow.run_local_server(port=8080)

        refresh_token = credentials.refresh_token

        return client_id, client_secret, refresh_token


def get_calendar_id():
    """Prompt for calendar ID."""
    print("\n" + "=" * 50)
    print("Calendar Selection")
    print("=" * 50)

    print("""
Which calendar should the display monitor?

- Enter "primary" for your main calendar (recommended)
- Or enter a specific calendar ID (found in calendar settings)
""")

    calendar_id = input("Calendar ID [primary]: ").strip() or "primary"
    return calendar_id


def generate_secrets_file(wifi_ssid, wifi_password, client_id, client_secret,
                          refresh_token, calendar_id):
    """Generate the secrets.py file."""

    content = f'''# Focus Display Secrets
# Auto-generated by setup_oauth.py
# DO NOT commit this file to version control!

# WiFi credentials
WIFI_SSID = "{wifi_ssid}"
WIFI_PASSWORD = "{wifi_password}"

# Google Calendar OAuth tokens
GOOGLE_CLIENT_ID = "{client_id}"
GOOGLE_CLIENT_SECRET = "{client_secret}"
GOOGLE_REFRESH_TOKEN = "{refresh_token}"

# Calendar to monitor
CALENDAR_ID = "{calendar_id}"
'''

    with open(SECRETS_FILE, "w") as f:
        f.write(content)

    print(f"\n✓ secrets.py generated at: {SECRETS_FILE}")


def main():
    print("""
╔═══════════════════════════════════════════════════════════╗
║           Focus Display - Setup Wizard                     ║
║                                                            ║
║  This wizard will configure your Inkplate focus display   ║
║  with WiFi and Google Calendar access.                    ║
╚═══════════════════════════════════════════════════════════╝
""")

    # Check if secrets.py already exists
    if SECRETS_FILE.exists():
        response = input("secrets.py already exists. Overwrite? [y/N]: ").strip().lower()
        if response != "y":
            print("Aborted.")
            sys.exit(0)

    # Gather information
    wifi_ssid, wifi_password = get_wifi_credentials()
    client_id, client_secret, refresh_token = get_google_credentials()
    calendar_id = get_calendar_id()

    # Generate secrets file
    generate_secrets_file(
        wifi_ssid, wifi_password,
        client_id, client_secret, refresh_token,
        calendar_id
    )

    print("""
╔═══════════════════════════════════════════════════════════╗
║                    Setup Complete!                         ║
╠═══════════════════════════════════════════════════════════╣
║                                                            ║
║  Next step: Upload to your Inkplate                       ║
║                                                            ║
║    python upload.py                                        ║
║                                                            ║
╚═══════════════════════════════════════════════════════════╝
""")


if __name__ == "__main__":
    main()

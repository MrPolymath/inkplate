# Focus Display - Specifications

## Overview

A minimalist e-ink display showing focus time and world clocks for a CEO's desk.

## Display Layout (1024x758 pixels - Inkplate 6PLUS)

### Normal Mode
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌──────────┐                                               │
│  │BARCELONA │                                               │
│  │  3:45 PM │         You can focus for the next           │
│  └──────────┘                                               │
│  ┌──────────┐              2h 34min                         │
│  │ NEW YORK │                                               │
│  │  9:45 AM │         ─────────────────────                 │
│  └──────────┘                                               │
│  ┌──────────┐         Next: Product sync @ 6:19 PM          │
│  │ SAN FRAN │                                               │
│  │  6:45 AM │                                               │
│  └──────────┘                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Evening Mode (after 7 PM, no meetings until next day)
```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌──────────┐                                               │
│  │BARCELONA │                                               │
│  │  8:15 PM │                                               │
│  └──────────┘                                               │
│  ┌──────────┐         Remember your priorities              │
│  │ NEW YORK │                                               │
│  │  2:15 PM │         ─────────────────────                 │
│  └──────────┘                                               │
│  ┌──────────┐         No meetings until tomorrow            │
│  │ SAN FRAN │                                               │
│  │ 11:15 AM │                                               │
│  └──────────┘                                               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Functional Requirements

### 1. World Clocks (Left Side)
- Three clocks displayed vertically
- Cities: Barcelona (local), New York, San Francisco
- Format: 12-hour with AM/PM (e.g., "3:45 PM")
- City name label above each time

### 2. Focus Timer (Center/Right)
- Main message: "You can focus for the next"
- Time display: "Xh Ymin" format (e.g., "2h 34min" or "45min" if < 1 hour)
- Shows next meeting title and time below

### 3. Evening Mode
- Activates after 7:00 PM Barcelona time
- Condition: No more meetings scheduled until next day
- Display: "Remember your priorities" instead of focus timer
- Subtext: "No meetings until tomorrow"

### 4. Calendar Integration
- Google Calendar API with OAuth 2.0
- Fetches events for current day + next day
- Refreshes calendar data every 15 minutes
- Only considers accepted meetings (not declined/tentative)

## Technical Specifications

### Hardware
- Inkplate 6PLUS (1024x758 pixels, 6" e-ink display with touchscreen)
- WiFi connected
- Battery powered

### Software
- MicroPython
- Inkplate MicroPython library

### Refresh Strategy (Battery Optimized)
- Screen refresh: Every 5 minutes
- Partial refresh: Default (fast, ~0.3s)
- Full refresh: Every 30 minutes (clears ghosting)
- Calendar API call: Every 15 minutes
- Deep sleep between refreshes to maximize battery life

### Timezones
- Local: Europe/Madrid (displayed as "Barcelona")
- New York: America/New_York
- San Francisco: America/Los_Angeles

## Setup

```bash
# 1. Install setup dependencies
cd focus-display/setup
pip install -r requirements.txt

# 2. Run OAuth setup (opens browser, you log in once)
python setup_oauth.py
# → Prompts for WiFi credentials
# → Opens browser for Google login
# → Generates ../secrets.py automatically

# 3. Connect Inkplate via USB and upload
python upload.py
# → Detects Inkplate
# → Uploads all .py files
# → Reboots device
```

## Maintenance
- **Change WiFi?** Edit secrets.py, run `python upload.py` again
- **Revoke access?** Go to Google Account → Security → Third-party apps
- **Update code?** Pull latest, run `python upload.py`

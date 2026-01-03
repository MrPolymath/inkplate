# Inkplate Projects

Monorepo for Inkplate 6PLUS e-ink display projects.

## Projects

### focus-display

CEO desk display showing focus time until next meeting and world clocks. Features:
- Three world clocks (Barcelona, New York, San Francisco)
- Focus timer showing available time until next meeting
- Google Calendar integration
- Battery indicator
- Evening mode with motivational message

See [focus-display/SPECS.md](focus-display/SPECS.md) for details.

## Shared Resources

- `fonts/` - Pre-rendered fonts (24px, 32px, 48px, bold variants)
- `shared/` - Reusable modules (battery indicator)

## Hardware

- **Device**: Inkplate 6PLUS (1024×758, touchscreen, front light)
- **Driver**: `inkplate6FLICK` MicroPython driver
- **Reference**: https://github.com/SolderedElectronics/Inkplate-micropython

## Development

See [CLAUDE.md](CLAUDE.md) for development commands and guidelines.

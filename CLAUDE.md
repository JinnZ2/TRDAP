# TRDAP - Transport Registration Data Access Protocol

## Project Overview

TRDAP is a lightweight, decentralized protocol for resource discovery and coordination between transportation hubs during emergencies and network outages. It enables hubs to share standardized resource data (fuel, medical supplies, transport capacity, shelter) over mesh networks including LoRa, Meshtastic, and ad-hoc WiFi.

This repository contains the protocol specification, reference implementations, deployment guides, and companion projects (Morse OS, Stranded Bible / ARK device, Rural Hub field kits).

## Repository Structure

```
TRDAP/
├── CLAUDE.md                                  # This file - project guide
├── README.md                                  # TRDAP protocol specification (IETF-style)
├── LICENSE                                    # CC0 1.0 Universal
│
├── docs/
│   ├── debugging-guide.md                     # Field debugging for rural hardware
│   └── morse-deployment-package.md            # Morse OS + assembly kits + mesh networking
│
├── stranded-bible/                            # "The Stranded Bible" / ARK device
│   ├── ark-system-design.md                   # PCB schematics, hardware architecture
│   ├── scrap-build-guide.md                   # Building components from salvaged materials
│   ├── content-and-hardware.md                # Sacred texts, survival content, device specs
│   └── development-plan.md                    # Dual-track development timeline
│
└── rural-hub/                                 # Rural community hub deployment
    ├── field-kit-deploy.md                    # Plug-and-play field kit ($150-200)
    ├── morse-integration.md                   # Morse code integration (light/audio/tactile/radio)
    ├── morse-os-complete.md                   # Complete Morse OS - all platforms
    └── pilot-program-100-kits.md              # 100-kit pilot assembly & support system
```

## Key Concepts

- **Transport Hub**: Physical facility (airport, train station, port, bus terminal) participating in the TRDAP network
- **Resource**: Any asset shareable between hubs (fuel, medical, transport, shelter, food, water, personnel)
- **Mesh Network**: Decentralized communication where each hub relays for others
- **Bootstrap Hub**: Maintains a registry and helps new hubs join
- **Morse OS**: Universal Morse code operating system across all platforms
- **The ARK**: Stranded Bible - offline spiritual/survival device for isolated persons

## Protocol Details

- **Transport**: UDP (preferred) or TCP
- **Max message size**: 512 bytes (LoRa-compatible)
- **Encoding**: JSON
- **Message types**: QUERY, RESPONSE, ANNOUNCE, PING, SYNC, REDIRECT, ERROR
- **Urgency levels**: critical, high, medium, low
- **Discovery**: LoRa/Meshtastic > WiFi ad-hoc > BLE > Audio > Optical (Morse)

## Naming Conventions

- **Files**: kebab-case (`morse-integration.md`, `field-kit-deploy.md`)
- **Directories**: kebab-case (`stranded-bible/`, `rural-hub/`)
- **Python classes**: PascalCase (`MorseOS`, `TRDAPHub`, `MorseLightBeacon`)
- **Python methods/variables**: snake_case (`text_to_morse_code`, `dot_duration`)
- **Python constants**: UPPER_SNAKE_CASE (`MORSE_PRIORITIES`, `SOS_PATTERN`)
- **JSON fields**: snake_case (`resource_type`, `message_id`, `hub_id`)
- **Resource types**: snake_case hierarchy (`fuel_jet_a`, `medical_kits`)
- **Hub types**: snake_case (`train_station`, `bus_terminal`, `ferry_terminal`)
- **Arduino constants**: UPPER_SNAKE_CASE (`LED`, `BUTTON`, `LIGHT_SENSOR`)

## Morse Code Timing Standard

All implementations must use these canonical values:

| Parameter       | Duration          | Notes                          |
|-----------------|-------------------|--------------------------------|
| Dot             | 0.2s (200ms)      | Base unit                      |
| Dash            | 0.6s (600ms)      | 3x dot                         |
| Symbol space    | 0.2s (200ms)      | Between dots/dashes in a letter|
| Letter space    | 0.6s (600ms)      | 3x dot                         |
| Word space      | 1.4s (1400ms)     | 7x dot                         |

Detection thresholds (for classifying input signals):

| Parameter       | Value             | Notes                          |
|-----------------|-------------------|--------------------------------|
| Dot max         | 0.35s (350ms)     | Signals <= 350ms are dots      |
| Dash min        | 0.35s (350ms)     | Signals > 350ms are dashes     |
| Letter gap      | 1.0s              | Gap indicating new letter      |
| Word gap        | 2.5s              | Gap indicating new word        |

**Important**: `dot_max` and `dash_min` must equal each other (no dead zone).

## Known Code Patterns & Pitfalls

1. **Method/attribute name collision**: Never name a method the same as a dict attribute. Use `decode_morse()` for the method and `morse_to_text_map` for the dict.
2. **Morse mapping duplication**: The canonical mapping is defined in `MorseOS.__init__()`. All other classes should inherit from `MorseOS` or accept the mapping as a parameter.
3. **GPIO cleanup**: Always call `GPIO.cleanup()` in finally blocks on Raspberry Pi.
4. **LoRa message size**: Keep TRDAP messages under 512 bytes for mesh compatibility.
5. **UUID format**: Use valid UUID v4 hex characters (0-9, a-f) in all examples.

## Development Workflow

1. All documentation is Markdown
2. Code examples are embedded in Markdown files (no standalone source files yet)
3. License: CC0 1.0 Universal (public domain)
4. Target audiences: rural communities, emergency responders, makers, IETF reviewers

## Testing Code Examples

Code in this repo is illustrative/reference. To validate:
- Python snippets: check syntax, import availability, class inheritance chains
- Arduino sketches: verify pin assignments, timing constants, serial baud rates
- HTML/JS: open in browser, check console for errors
- KiCad schematics: verify pin assignments against datasheets

# UE Mini Boom Controller — User Guide

## Purpose

This Python tool fully replaces the official **UE MINI BOOM** app (iOS/Android), which is no longer maintained and nearly impossible to find. It communicates directly with the speaker over Bluetooth using the reverse-engineered protocol from the UE Boom family.

---

## Replicated Features

| Feature | Original App | This Tool | Method |
|---|---|---|---|
| Double Up (2 speakers, same audio) | ✅ | ✅ (+ hardware buttons) | SPP / Buttons |
| **Stereo Mode (L/R)** | ✅ | ✅ | SPP — **software only** |
| Rename speaker | ✅ | ✅ | SPP |
| Battery level | ✅ | ✅ | D-Bus |
| Remote power on/off | ❌ | ✅ bonus! | BLE GATT |

Features in **bold** require software — hardware buttons alone are not enough.

---

## Prerequisites

### Hardware
- A computer with Bluetooth (Linux recommended, macOS/Windows possible)
- Your UE Mini Boom, powered on and paired

### Software

**Linux (recommended):**
```bash
sudo apt install python3 python3-pip libbluetooth-dev bluetooth bluez
pip install pybluez bleak
```

**macOS:**
```bash
pip3 install bleak
# pybluez doesn't work well on macOS
# Use BLE commands only (battery, power on/off, info)
# For SPP commands (EQ, stereo), use Linux
```

**Windows:**
```bash
pip install pybluez bleak
```

**Raspberry Pi (ideal as a dedicated controller):**
```bash
sudo apt install python3-pip libbluetooth-dev bluetooth bluez
pip3 install pybluez bleak --break-system-packages
```

---

## Tab Completion

The `ueboom` command supports argument completion with Tab.

**Bash:**
```bash
# Enable for the current session
eval "$(register-python-argcomplete ueboom)"

# Enable permanently — add to ~/.bashrc
echo 'eval "$(register-python-argcomplete ueboom)"' >> ~/.bashrc
```

**Zsh:**
```bash
# Add to ~/.zshrc
autoload -U bashcompinit && bashcompinit
eval "$(register-python-argcomplete ueboom)"
```

**Fish:**
```fish
register-python-argcomplete --shell fish ueboom | source

# Permanent — save to Fish completions
register-python-argcomplete --shell fish ueboom > ~/.config/fish/completions/ueboom.fish
```

**Global activation (all argcomplete commands):**
```bash
activate-global-python-argcomplete
```

Once enabled, `ueboom --<Tab>` completes flags (`--battery`, `--stereo-setup`, etc.).

---

## Quick Start

### 1. Find your speaker's MAC address

```bash
# List paired UE speakers
ueboom --list

# Or via Linux Bluetooth tools
bluetoothctl
> scan on
# Look for "UE MINI BOOM" in the list
> scan off
> quit
```

### 2. Pair the speaker (if not already done)

```bash
bluetoothctl
> power on
> agent on
> scan on
# Wait for the speaker's MAC address to appear
> pair XX:XX:XX:XX:XX:XX
> trust XX:XX:XX:XX:XX:XX
> connect XX:XX:XX:XX:XX:XX
> quit
```

### 3. Send commands

```bash
# Check battery
ueboom --battery

# Show full speaker status
ueboom --status

# Guided stereo pairing setup
ueboom --stereo-setup

# Interactive mode (full menu)
ueboom -i
```

If only one UE speaker is paired, the MAC address is auto-detected. Otherwise, specify it with `--mac XX:XX:XX:XX:XX:XX`.

---

## Interactive Mode

The `-i` or `--interactive` flag launches a full text menu:

```
╔══════════════════════════════════════════════════╗
║         UE Mini Boom Controller v1.0             ║
╚══════════════════════════════════════════════════╝

=== Stereo / Double Up ===
  1) Set mode: Stereo (L/R channels)
  2) Set mode: Double (same audio)
  3) Set this speaker as LEFT channel
  4) Set this speaker as RIGHT channel
  ...

=== Other ===
  7) Announce battery level (audible)
  8) Set speaker name
  9) Play power-on sound
```

---

## Double Up / Stereo Setup

### Without the tool (buttons only) — Double Up (mono) only
1. Press **Volume+ and Bluetooth** simultaneously on the playing speaker
2. Press the **Bluetooth button twice** on the second speaker
3. Both speakers play the same audio (no stereo L/R separation)

### With the tool — guided stereo setup
```bash
ueboom --stereo-setup
```
The tool guides you through the steps:
1. Confirmation before initiating discovery mode
2. The connected speaker enters discovery mode (fast blinking)
3. Instructions for the second speaker (turn on, press Bluetooth button twice)
4. Wait for both speakers to stop blinking (lights go solid)
5. Choose left/right channel for the connected speaker

> **Note:** If the lights on both speakers turn off instead of going solid, the pairing timed out. Run `ueboom --stereo-setup` again — it may take a few attempts.

---

## Protocol Details

### SPP Communication (Serial Port Profile)

The speaker exposes an RFCOMM service named **"LWACP"** (Logitech Wireless Audio Control Protocol) on the standard SPP UUID `00001101-0000-1000-8000-00805F9B34FB`.

Packet format:
```
[total_length] [0x01] [command_id] [param1] [param2] ...
```

Where `total_length = 1 + 1 + number_of_parameters`

### Known Commands

| Command | Hex ID | Parameters | Effect |
|---|---|---|---|
| EQ Preset | `0x64` | `00`=off, `01`=OutLoud, `02`=Intimate, `03`=Vocals | Change EQ |
| Sonification | `0x65` | `00`=off, `01`=on | Alert sounds |
| Double Up Mode | `0x67` | `00`=double, `01`=stereo | Multi-speaker mode |
| Double Up Role | `0x68` | `00`=left, `01`=right | L/R channel |
| Double Up Lock | `0x69` | `00`=off, `01`=on | Auto-reconnect |
| Battery Announce | `0x6B` | (none) | Audible battery announcement |
| Emit Sound | `0x6C` | `60 C0` | Power-on sound |
| Set Name | `0x72` | UTF-8 bytes | Rename the speaker |
| Volume | `0xBB` | `01 01`=up, `00 01`=down | Adjust volume |
| BLE State | `0xB9` | `00`=off, `01`=on | Toggle BLE |

### BLE GATT Communication

Documented characteristics:

| UUID | Function | R/W |
|---|---|---|
| `c6d6dc0d-07f5-47ef-9b59-630622b01fd3` | Power on/off | Write |
| `00002a19-0000-1000-8000-00805f9b34fb` | Battery level | Read |
| `00002a00-0000-1000-8000-00805f9b34fb` | Device name | Read |
| `00002a28-0000-1000-8000-00805f9b34fb` | Firmware version | Read |
| `00002a25-0000-1000-8000-00805f9b34fb` | Serial number | Read |
| `54f7f292-7ebb-4267-83c2-8e6ee7e881ff` | Color | Read |
| `16e005bb-3862-43c7-8f5c-6f654a4ffdd2` | Alarm | R/W |

---

## Important Notes

### Mini Boom vs Boom Compatibility
The protocol comes from reverse-engineering the UE Boom / Boom 2, which share the same Logitech software base (package `com.logitech.ue.centurion`). The Mini Boom uses the same LWACP protocol, but as an older and simpler product, some advanced commands (firmware update, PartyUp 50+ speakers) do not apply.

### EQ Commands — Important
The EQ preset IDs (`0x64` with parameters `01/02/03`) are extrapolated from the Boom protocol. If the presets don't match exactly on the Mini Boom, you would need to capture real Bluetooth traffic with the original app to confirm the exact values. See the "Calibration" section below.

### Calibration (if needed)
If a command doesn't work as expected:

1. **On Android**: Enable HCI Bluetooth logging in Developer Options
2. Launch the UE Mini Boom app (APK 1.2.29 available on APKPure/APKMirror)
3. Perform the desired action (change EQ, enable stereo...)
4. Retrieve the log: `adb pull /sdcard/btsnoop_hci.log`
5. Open in Wireshark, filter on RFCOMM
6. Identify the exact bytes sent
7. Adjust the constants in the code

---

## Sources and Credits

- [countableSet/ue-boom-re](https://github.com/countableSet/ue-boom-re) — Reverse engineering SPP commands
- [kancelott/ue-boom-2-bt-le-reverse-engineering](https://github.com/kancelott/ue-boom-2-bt-le-reverse-engineering) — BLE GATT characteristics
- [skilo-sh/Reversing-UE-Boom](https://github.com/skilo-sh/Reversing-UE-Boom) — Python D-Bus control
- [marcust/gist](https://gist.github.com/marcust/af93ff47899583f5a52f) — BLE power on via gatttool
- [Blog countableset](https://blog.countableset.com/2022/02/22/ue-boom-reverse-engineering/) — Detailed write-up

---

## License

MIT — For personal use with your own UE Mini Boom hardware.

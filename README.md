# UE Mini Boom Controller

## Purpose

The official **UE MINI BOOM** app (iOS/Android) is no longer maintained and nearly impossible to find. Without it, **stereo mode (L/R separation) is impossible** — hardware buttons only support Double Up (mono on both speakers).

This Linux command-line tool replaces the app. Its main goal is to provide the ability to **set up stereo mode** between two UE Mini Boom speakers. It also offers battery readout, speaker renaming, and a few other utilities.

---

## Features

| Feature | Method | Notes |
|---|---|---|
| **Stereo setup** (guided pairing of two speakers) | SPP | Main feature — software only, no app needed |
| Battery level | D-Bus | Instant, no BLE scan needed |
| Speaker status (connection, battery, EQ) | D-Bus + SPP | |
| Rename speaker | SPP | |
| Audible battery announcement | SPP | Speaker announces level out loud |
| Play power-on sound | SPP | |
| Send raw commands | SPP | For advanced users / debugging |

---

## Prerequisites

- **Linux** with BlueZ (tested on Debian/Kali)
- Python 3.10+
- Your UE Mini Boom, powered on and paired via `bluetoothctl`

### Install

```bash
sudo apt install python3 python3-pip libbluetooth-dev bluetooth bluez
git clone https://github.com/carreolivierwork/ue-mini-boom-manager.git
cd ue-mini-boom-manager
pip install -e .
```

---

## Quick Start

### 1. Pair the speaker (if not already done)

```bash
bluetoothctl
> power on
> agent on
> scan on
# Wait for "UE MINI BOOM" to appear
> pair XX:XX:XX:XX:XX:XX
> trust XX:XX:XX:XX:XX:XX
> connect XX:XX:XX:XX:XX:XX
> quit
```

### 2. Use the tool

```bash
# List paired UE speakers
ueboom --list

# Check battery
ueboom --battery

# Show full speaker status
ueboom --status

# Guided stereo setup (two speakers)
ueboom --stereo-setup

# Rename the speaker
ueboom --name "My Speaker"

# Interactive mode
ueboom -i

# Send a raw hex command
ueboom --raw "02 01 6B"
```

If only one UE speaker is paired, the MAC address is auto-detected. Otherwise, specify it with `--mac XX:XX:XX:XX:XX:XX`.

---

## Stereo Setup

### Why you need this tool

The hardware buttons on the UE Mini Boom only support **Double Up** (same mono audio on both speakers). **Stereo mode** (left/right channel separation) requires software commands that were only available through the original app.

### Without the tool (buttons only) — Double Up (mono)

1. Press **Volume+ and Bluetooth** simultaneously on the playing speaker
2. Press the **Bluetooth button twice** on the second speaker
3. Both speakers play the same audio (no L/R separation)

### With the tool — Stereo setup

```bash
ueboom --stereo-setup
```

The tool guides you through the process:

1. Confirm to initiate discovery mode
2. The connected speaker enters discovery mode (fast blinking)
3. On the second speaker: turn it on, press the Bluetooth button twice
4. Wait for both speakers to stop blinking (lights go solid)
5. Confirm the pairing succeeded

If both lights turn off instead of going solid, the pairing timed out. Run `ueboom --stereo-setup` again — it may take a few attempts.

---

## Tab Completion

```bash
# Bash — add to ~/.bashrc
eval "$(register-python-argcomplete ueboom)"

# Zsh — add to ~/.zshrc
autoload -U bashcompinit && bashcompinit
eval "$(register-python-argcomplete ueboom)"
```

---

## Protocol Reference

### SPP (Serial Port Profile)

The speaker exposes an RFCOMM service named **LWACP** (Logitech Wireless Audio Control Protocol).

Packet format: `[total_length] [0x01] [command_id] [params...]`

| Command | Hex ID | Parameters | Notes |
|---|---|---|---|
| EQ Preset | `0x64` | `00`-`03` | Read-only query works |
| Sonification | `0x65` | `00`=off, `01`=on | |
| Double Up Mode | `0x67` | `00`=double, `01`=stereo | |
| Double Up Role | `0x68` | `00`=left, `01`=right | |
| Double Up Lock | `0x69` | query (no params) triggers discovery | |
| Battery Announce | `0x6B` | (none) | Audible announcement |
| Emit Sound | `0x6C` | `60 C0` | Power-on sound |
| Set Name | `0x72` | UTF-8 bytes | Max 32 bytes |
| BLE State | `0xB9` | `00`=off, `01`=on | |
| Volume | `0xBB` | `01 01`=up, `00 01`=down | |

> **Note:** Many commands are documented from reverse-engineering the UE Boom / Boom 2 (same LWACP protocol). Not all of them work reliably on the Mini Boom. The `--raw` flag lets you experiment with any command.

---

## Sources

- [countableSet/ue-boom-re](https://github.com/countableSet/ue-boom-re) — SPP command reverse engineering
- [kancelott/ue-boom-2-bt-le-reverse-engineering](https://github.com/kancelott/ue-boom-2-bt-le-reverse-engineering) — BLE GATT characteristics
- [skilo-sh/Reversing-UE-Boom](https://github.com/skilo-sh/Reversing-UE-Boom) — Python D-Bus control
- [Blog countableset](https://blog.countableset.com/2022/02/22/ue-boom-reverse-engineering/) — Detailed write-up

---

## License

MIT — For personal use with your own UE Mini Boom hardware.

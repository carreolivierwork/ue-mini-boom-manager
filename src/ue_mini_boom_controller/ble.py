"""BlueZ D-Bus transport and device discovery for UE Mini Boom."""

import subprocess

from .protocol import UE_NAME_KEYWORDS, UE_OUI_PREFIXES


def get_device_status(speaker_mac: str) -> dict:
    """Read device status from BlueZ via bluetoothctl.

    Returns a dict with available fields: name, connected, paired, battery.
    """
    info = {}
    try:
        result = subprocess.run(
            ["bluetoothctl", "info", speaker_mac],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return info

    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("Name:"):
            info["name"] = line.split(":", 1)[1].strip()
        elif line.startswith("Alias:"):
            alias = line.split(":", 1)[1].strip()
            # Only store alias if it differs from name
            if alias != info.get("name"):
                info["alias"] = alias
        elif line.startswith("Connected:"):
            info["connected"] = line.split(":")[1].strip() == "yes"
        elif line.startswith("Paired:"):
            info["paired"] = line.split(":")[1].strip() == "yes"
        elif line.startswith("Modalias:"):
            # Format: "usb:v046DpBA20dFF0A" -> vendor, product, version
            raw = line.split(":", 1)[1].strip()
            info["modalias"] = raw
        elif line.startswith("Battery Percentage:"):
            # Format: "Battery Percentage: 0x64 (100)"
            try:
                info["battery"] = int(line.split("(")[1].rstrip(")"))
            except (IndexError, ValueError):
                pass
    return info


def get_battery(speaker_mac: str) -> int:
    """Read battery level from BlueZ D-Bus Battery1 interface.

    Returns battery percentage (0-100) or -1 on failure.
    """
    dbus_path = "/org/bluez/hci0/dev_" + speaker_mac.replace(":", "_")
    try:
        result = subprocess.run(
            [
                "dbus-send",
                "--system",
                "--print-reply",
                "--dest=org.bluez",
                dbus_path,
                "org.freedesktop.DBus.Properties.Get",
                "string:org.bluez.Battery1",
                "string:Percentage",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                line = line.strip()
                if line.startswith("variant") or "byte" in line:
                    parts = line.split()
                    return int(parts[-1])
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass
    return -1


def is_ue_device(address: str, name: str) -> bool:
    """Check if a Bluetooth device is a UE speaker by name keywords or OUI prefix."""
    upper_name = name.upper()
    if any(kw in upper_name for kw in UE_NAME_KEYWORDS):
        return True
    return any(address.upper().startswith(p.upper()) for p in UE_OUI_PREFIXES)


def get_paired_ue_devices() -> list[tuple[str, str]]:
    """Return paired UE speakers as a list of (mac_address, name) tuples."""
    try:
        result = subprocess.run(
            ["bluetoothctl", "devices", "Paired"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except FileNotFoundError:
        return []

    devices = []
    for line in result.stdout.splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) < 3 or parts[0] != "Device":
            continue
        address = parts[1]
        name = parts[2]
        if is_ue_device(address, name):
            devices.append((address, name))
    return devices

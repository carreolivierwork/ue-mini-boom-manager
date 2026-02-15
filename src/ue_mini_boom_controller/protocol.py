"""
Protocol constants and command builder for UE Mini Boom.

Extracted from decompiled UE Boom APK (com.logitech.ue.centurion.*).
"""

# Bluetooth SPP UUID (Serial Port Profile — standard)
SPP_UUID = "00001101-0000-1000-8000-00805F9B34FB"

# BLE GATT Characteristics (from UE Boom BLE reverse engineering)
BLE_SERVICE_UUID = "000061fe-0000-1000-8000-00805f9b34fb"
BLE_POWER_UUID = "c6d6dc0d-07f5-47ef-9b59-630622b01fd3"
BLE_BATTERY_UUID = "00002a19-0000-1000-8000-00805f9b34fb"
BLE_NAME_UUID = "00002a00-0000-1000-8000-00805f9b34fb"
BLE_FW_VERSION_UUID = "00002a28-0000-1000-8000-00805f9b34fb"
BLE_SERIAL_UUID = "00002a25-0000-1000-8000-00805f9b34fb"
BLE_COLOR_UUID = "54f7f292-7ebb-4267-83c2-8e6ee7e881ff"
BLE_ALARM_UUID = "16e005bb-3862-43c7-8f5c-6f654a4ffdd2"

# Known OUI prefixes for UE / Logitech devices (first 3 bytes of MAC address).
# Used to identify renamed speakers that no longer have "UE" or "BOOM" in their name.
UE_OUI_PREFIXES = [
    "88:C6:26",  # UE Mini Boom / UE Boom
    "38:F0:C8",  # Logitech
    "44:73:D6",  # Logitech
    "94:02:30",  # Logitech
    "C8:DB:26",  # Logitech
]

# Keywords to match in device names (case-insensitive).
# Used alongside OUI prefixes to identify UE speakers that may have been renamed.
UE_NAME_KEYWORDS = ["UE", "BOOM", "MINI"]


class UECommand:
    """
    Known SPP commands extracted from the decompiled UE Boom APK.

    Source: com.logitech.ue.centurion.device.command.UEDeviceCommand.UECommand
    """

    # === Volume ===
    # Parameters: [direction: 0x01=up, 0x00=down] [step: usually 0x01]
    VOLUME_ADJUST = 0xBB

    # === Battery ===
    # No parameters — speaker announces battery level audibly
    BATTERY_ANNOUNCE = 0x6B

    # === Sonification (alert sounds) ===
    # Parameters: [0x00=off, 0x01=conga, etc.]
    SONIFICATION = 0x65

    # === Sound Effects ===
    # Parameters: [sound_id_high] [sound_id_low]
    EMIT_SOUND = 0x6C

    # === BLE State ===
    # Parameters: [0x00=off, 0x01=on]
    BLE_STATE = 0xB9

    # === EQ Preset ===
    # Parameters: [preset_id]
    # Known presets for Mini Boom:
    #   0x00 = Off / Flat
    #   0x01 = Out Loud (bass boost)
    #   0x02 = Intimate (reduced bass)
    #   0x03 = Vocals (mid boost)
    EQ_PRESET = 0x64

    # === Speaker Name ===
    # Parameters: [name bytes as UTF-8]
    SET_NAME = 0x72

    # === Double Up / Stereo ===
    #   DOUBLE_UP_MODE: [0x00=double (mono), 0x01=stereo]
    #   DOUBLE_UP_ROLE: [0x00=left, 0x01=right]
    DOUBLE_UP_MODE = 0x67
    DOUBLE_UP_ROLE = 0x68
    DOUBLE_UP_LOCK = 0x69  # [0x00=off, 0x01=on] — auto-reconnect


def build_spp_command(command_id: int, *params: int) -> bytes:
    """
    Build an SPP command packet.

    Format: [total_length] [0x01] [command_id] [param1] [param2] ...

    total_length = 1 (constant 0x01) + 1 (command_id) + len(params)
    """
    payload = bytes([0x01, command_id] + list(params))
    length = len(payload)
    return bytes([length]) + payload


# Pre-built commands
COMMANDS = {
    # Battery
    "battery_announce": build_spp_command(UECommand.BATTERY_ANNOUNCE),
    # Sound effects
    "sound_power_on": build_spp_command(UECommand.EMIT_SOUND, 0x60, 0xC0),
    # Double Up modes
    "mode_double": build_spp_command(UECommand.DOUBLE_UP_MODE, 0x00),
    "mode_stereo": build_spp_command(UECommand.DOUBLE_UP_MODE, 0x01),
    # Stereo discovery trigger (querying DU lock initiates pairing workflow)
    "stereo_discover": build_spp_command(UECommand.DOUBLE_UP_LOCK),
    # Stereo role assignment
    "role_left": build_spp_command(UECommand.DOUBLE_UP_ROLE, 0x00),
    "role_right": build_spp_command(UECommand.DOUBLE_UP_ROLE, 0x01),
    # Double Up auto-reconnect lock
    "doubleup_lock_off": build_spp_command(UECommand.DOUBLE_UP_LOCK, 0x00),
    "doubleup_lock_on": build_spp_command(UECommand.DOUBLE_UP_LOCK, 0x01),
}

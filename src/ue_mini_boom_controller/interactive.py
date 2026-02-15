"""Interactive menu mode for UE Mini Boom."""

from .protocol import COMMANDS
from .spp import send_spp_command, set_speaker_name


def interactive_mode(mac_address: str):
    """Run an interactive menu for controlling the speaker."""
    print(f"""
\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557
\u2551         UE Mini Boom Controller v1.0             \u2551
\u2551         Speaker: {mac_address}       \u2551
\u255a\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255d

=== EQ Presets ===
  1) EQ: Out Loud (bass boost)
  2) EQ: Intimate (reduced bass)
  3) EQ: Vocals (mid boost)
  4) EQ: Off (flat)

=== Stereo / Double Up ===
  5) Set mode: Stereo (L/R channels)
  6) Set mode: Double (same audio)
  7) Set this speaker as LEFT channel
  8) Set this speaker as RIGHT channel
  9) Double Up auto-reconnect: ON
 10) Double Up auto-reconnect: OFF

=== Other ===
 11) Announce battery level (audible)
 12) Volume up
 13) Volume down
 14) Alerts ON
 15) Alerts OFF
 16) BLE ON
 17) BLE OFF
 18) Set speaker name
 19) Play power-on sound

  0) Quit
""")

    command_map = {
        "1": "eq_outloud",
        "2": "eq_intimate",
        "3": "eq_vocals",
        "4": "eq_off",
        "5": "mode_stereo",
        "6": "mode_double",
        "7": "role_left",
        "8": "role_right",
        "9": "doubleup_lock_on",
        "10": "doubleup_lock_off",
        "11": "battery_announce",
        "12": "volume_up",
        "13": "volume_down",
        "14": "alerts_on",
        "15": "alerts_off",
        "16": "ble_on",
        "17": "ble_off",
        "19": "sound_power_on",
    }

    while True:
        try:
            choice = input("\nCommand> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if choice == "0":
            print("Goodbye!")
            break
        elif choice == "18":
            name = input("Enter new speaker name: ").strip()
            if name:
                set_speaker_name(mac_address, name)
        elif choice in command_map:
            cmd_name = command_map[choice]
            cmd = COMMANDS[cmd_name]
            send_spp_command(mac_address, cmd)
        else:
            print("Invalid choice.")

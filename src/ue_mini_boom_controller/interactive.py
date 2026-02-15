"""Interactive menu mode for UE Mini Boom."""

from .protocol import COMMANDS
from .spp import send_spp_command, set_speaker_name


def interactive_mode(mac_address: str):
    """Run an interactive menu for controlling the speaker."""
    print(f"""
╔══════════════════════════════════════════════════╗
║         UE Mini Boom Controller v1.0             ║
║         Speaker: {mac_address}       ║
╚══════════════════════════════════════════════════╝

=== Stereo / Double Up ===
  1) Set mode: Stereo (L/R channels)
  2) Set mode: Double (same audio)
  3) Set this speaker as LEFT channel
  4) Set this speaker as RIGHT channel
  5) Double Up auto-reconnect: ON
  6) Double Up auto-reconnect: OFF

=== Other ===
  7) Announce battery level (audible)
  8) Set speaker name
  9) Play power-on sound

  0) Quit
""")

    command_map = {
        "1": "mode_stereo",
        "2": "mode_double",
        "3": "role_left",
        "4": "role_right",
        "5": "doubleup_lock_on",
        "6": "doubleup_lock_off",
        "7": "battery_announce",
        "9": "sound_power_on",
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
        elif choice == "8":
            name = input("Enter new speaker name: ").strip()
            if name:
                set_speaker_name(mac_address, name)
        elif choice in command_map:
            cmd_name = command_map[choice]
            cmd = COMMANDS[cmd_name]
            send_spp_command(mac_address, cmd)
        else:
            print("Invalid choice.")

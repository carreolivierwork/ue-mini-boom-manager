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

  1) Announce battery level (audible)
  2) Set speaker name
  3) Play power-on sound

  0) Quit
""")

    command_map = {
        "1": "battery_announce",
        "3": "sound_power_on",
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
        elif choice == "2":
            name = input("Enter new speaker name: ").strip()
            if name:
                set_speaker_name(mac_address, name)
        elif choice in command_map:
            cmd_name = command_map[choice]
            cmd = COMMANDS[cmd_name]
            send_spp_command(mac_address, cmd)
        else:
            print("Invalid choice.")

"""CLI entry point for UE Mini Boom Controller."""

import argparse
import time

import argcomplete

from .ble import get_battery, get_device_status, get_paired_ue_devices
from .interactive import interactive_mode
from .protocol import COMMANDS, UECommand
from .spp import query_spp_values, send_spp_command, set_speaker_name

_EQ_NAMES = {0: "Off (flat)", 1: "Out Loud", 2: "Intimate", 3: "Vocals"}


def _print_status(mac: str):
    """Print current speaker status from BlueZ D-Bus + safe LWACP queries."""
    status = get_device_status(mac)

    name = status.get("name", mac)
    connected = status.get("connected", False)
    paired = status.get("paired", False)
    battery = status.get("battery")
    modalias = status.get("modalias", "")

    print(f"=== {name} ({mac}) ===")
    print(f"  Paired:     {'yes' if paired else 'no'}")
    print(f"  Connected:  {'yes' if connected else 'no'}")
    if battery is not None:
        print(f"  Battery:    {battery}%")
    if modalias:
        print(f"  Modalias:   {modalias}")

    if not connected:
        print("  (connect the speaker to read more parameters)")
        return

    # Query EQ preset over LWACP (safe to read)
    values = query_spp_values(mac, [UECommand.EQ_PRESET])

    eq_val = values.get(UECommand.EQ_PRESET)
    if eq_val is not None:
        print(f"  EQ Preset:  {_EQ_NAMES.get(eq_val, f'Unknown ({eq_val})')}")


def _stereo_setup_flow(mac: str):
    """Guided stereo pairing setup for two UE Mini Boom speakers."""
    stereo_sent = False
    try:
        print("=== Stereo Setup ===")
        print("This will put the connected speaker into pairing/discovery mode.")
        confirm = input("Continue? [y/N]: ").strip().lower()
        if confirm not in ("y", "yes"):
            print("Setup cancelled.")
            return

        print()
        print("Step 1: Initiating stereo discovery on the connected speaker...")
        if not send_spp_command(mac, COMMANDS["stereo_discover"], verbose=False):
            print("ERROR: Failed to send stereo command. Is the speaker connected?")
            return
        stereo_sent = True

        print("The connected speaker is now in discovery mode (fast blinking).")
        print()
        print("Step 2: On the second speaker:")
        print("  1. Turn it on")
        print("  2. Press the Bluetooth button twice")
        print("  3. Wait for it to start blinking fast")
        print("  4. Wait for both speakers to stop blinking (lights go solid)")
        print()
        print("  Note: If both lights turn off instead of going solid,")
        print("  the pairing timed out. Re-run --stereo-setup and try again.")
        print()
        input("Press Enter when both speakers have solid lights...")
        print()
        print("Step 3: Assigning connected speaker as LEFT channel...")
        time.sleep(1.0)
        if not send_spp_command(mac, COMMANDS["role_left"], verbose=False):
            print("ERROR: Failed to assign stereo role.")
            return

        print("Stereo setup complete! Connected speaker is LEFT, second speaker is RIGHT.")

    except (KeyboardInterrupt, EOFError):
        print("\nSetup cancelled.")
        if stereo_sent:
            print("WARNING: Speaker may still be in discovery mode. Power-cycle to reset.")


def main():
    parser = argparse.ArgumentParser(
        description="UE Mini Boom Controller \u2014 replaces the official app",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List paired UE speakers
  %(prog)s --list

  # Show speaker status (battery, EQ, connection)
  %(prog)s --status

  # Check battery (auto-detects speaker if only one paired)
  %(prog)s --battery

  # Guided stereo pairing setup
  %(prog)s --stereo-setup

  # Interactive mode
  %(prog)s -i
        """,
    )

    parser.add_argument("--mac", help="Bluetooth MAC address of the UE Mini Boom")
    parser.add_argument("--list", action="store_true", help="List paired UE speakers")
    parser.add_argument("--status", action="store_true", help="Show current speaker status")
    parser.add_argument("--battery", action="store_true", help="Read battery level")
    parser.add_argument(
        "--stereo-setup",
        action="store_true",
        help="Guided stereo pairing setup for two speakers",
    )
    parser.add_argument("--name", help="Set speaker name")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive menu mode")
    parser.add_argument("--raw", help="Send raw hex command (e.g. '03 01 64 01')")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    # --- List paired UE speakers (no MAC needed) ---
    if args.list:
        devices = get_paired_ue_devices()
        if devices:
            print(f"Found {len(devices)} paired UE speaker(s):")
            for addr, name in devices:
                print(f"  {addr}  {name}")
        else:
            print("No paired UE speakers found.")
            print("Pair your speaker first: bluetoothctl pair <MAC>")
        return

    # --- Auto-detect MAC if not provided ---
    if not args.mac:
        devices = get_paired_ue_devices()
        if len(devices) == 1:
            mac = devices[0][0]
            print(f"Auto-detected: {devices[0][1]} ({mac})")
        elif len(devices) > 1:
            print(f"Multiple UE speakers found ({len(devices)}). Specify --mac:")
            for addr, name in devices:
                print(f"  {addr}  {name}")
            return
        else:
            parser.print_help()
            return
    else:
        mac = args.mac

    # --- Status ---
    if args.status:
        _print_status(mac)
        return

    # --- Battery ---
    if args.battery:
        level = get_battery(mac)
        if level >= 0:
            print(f"Battery: {level}%")
        else:
            print("Could not read battery. Is the speaker connected?")
        return

    # --- SPP commands ---
    if args.stereo_setup:
        _stereo_setup_flow(mac)

    elif args.name:
        set_speaker_name(mac, args.name)

    elif args.raw:
        raw_bytes = bytes.fromhex(args.raw.replace(" ", ""))
        send_spp_command(mac, raw_bytes)

    elif args.interactive:
        interactive_mode(mac)

    else:
        parser.print_help()

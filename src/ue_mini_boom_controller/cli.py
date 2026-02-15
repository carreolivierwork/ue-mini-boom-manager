"""CLI entry point for UE Mini Boom Controller."""

import argparse
import time

import argcomplete

from .ble import get_battery, get_device_status, get_paired_ue_devices
from .interactive import interactive_mode
from .protocol import COMMANDS, UECommand
from .spp import query_spp_values, send_spp_command, set_speaker_name

_EQ_NAMES = {0: "Off (flat)", 1: "Out Loud", 2: "Intimate", 3: "Vocals"}
_ALERT_NAMES = {0: "Off", 1: "On (conga)", 2: "On (default)"}


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

    # Query multiple values over LWACP in a single connection (safe pacing)
    values = query_spp_values(mac, [
        UECommand.EQ_PRESET,
        UECommand.SONIFICATION,
        UECommand.VOLUME_ADJUST,
    ])

    eq_val = values.get(UECommand.EQ_PRESET)
    if eq_val is not None:
        print(f"  EQ Preset:  {_EQ_NAMES.get(eq_val, f'Unknown ({eq_val})')}")

    alert_val = values.get(UECommand.SONIFICATION)
    if alert_val is not None:
        print(f"  Alerts:     {_ALERT_NAMES.get(alert_val, f'Unknown ({alert_val})')}")

    vol_val = values.get(UECommand.VOLUME_ADJUST)
    if vol_val is not None:
        print(f"  Volume:     {vol_val}")


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
        if not send_spp_command(mac, COMMANDS["mode_stereo"], verbose=False):
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
        input("Press Enter when both speakers have solid lights...")
        print()
        print("Step 3: Assigning stereo roles...")
        role_input = input(
            "Which channel is the CONNECTED speaker? [L]eft / (r)ight: "
        ).strip().lower()
        if role_input in ("r", "right"):
            role_name = "right"
        elif role_input in ("", "l", "left"):
            role_name = "left"
        else:
            print(f"Unrecognized input '{role_input}', defaulting to left.")
            role_name = "left"

        time.sleep(1.0)
        if not send_spp_command(mac, COMMANDS[f"role_{role_name}"], verbose=False):
            print("ERROR: Failed to assign stereo role.")
            return

        print(f"Assigned connected speaker to: {role_name}")
        print("Stereo setup complete! Use '--mode stereo' or '--mode double' to switch modes.")

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

  # Set EQ to "Out Loud" (bass boost)
  %(prog)s --mac 88:C6:26:XX:XX:XX --eq outloud

  # Guided stereo pairing setup
  %(prog)s --mac 88:C6:26:XX:XX:XX --stereo-setup

  # Interactive mode
  %(prog)s --mac 88:C6:26:XX:XX:XX --interactive

EQ presets: outloud, intimate, vocals, off
Stereo roles: left, right
Modes: stereo, double
        """,
    )

    parser.add_argument("--mac", help="Bluetooth MAC address of the UE Mini Boom")
    parser.add_argument("--list", action="store_true", help="List paired UE speakers")
    parser.add_argument("--status", action="store_true", help="Show current speaker status")
    parser.add_argument("--battery", action="store_true", help="Read battery level")
    parser.add_argument(
        "--eq",
        choices=["outloud", "intimate", "vocals", "off"],
        help="Set EQ preset",
    )
    parser.add_argument(
        "--stereo",
        choices=["left", "right"],
        help="Set stereo mode and assign L/R role",
    )
    parser.add_argument(
        "--stereo-setup",
        action="store_true",
        help="Guided stereo pairing setup for two speakers",
    )
    parser.add_argument("--mode", choices=["stereo", "double"], help="Set Double Up mode")
    parser.add_argument("--alerts", choices=["on", "off"], help="Toggle alert sounds")
    parser.add_argument("--ble", choices=["on", "off"], help="Toggle BLE state")
    parser.add_argument("--volume", choices=["up", "down"], help="Adjust volume")
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
    if args.eq:
        send_spp_command(mac, COMMANDS[f"eq_{args.eq}"])

    elif args.stereo_setup:
        _stereo_setup_flow(mac)

    elif args.stereo:
        print("Setting stereo mode...")
        send_spp_command(mac, COMMANDS["mode_stereo"])
        time.sleep(0.5)
        print(f"Setting role: {args.stereo}...")
        send_spp_command(mac, COMMANDS[f"role_{args.stereo}"])

    elif args.mode:
        send_spp_command(mac, COMMANDS[f"mode_{args.mode}"])

    elif args.alerts:
        send_spp_command(mac, COMMANDS[f"alerts_{args.alerts}"])

    elif args.ble:
        send_spp_command(mac, COMMANDS[f"ble_{args.ble}"])

    elif args.volume:
        send_spp_command(mac, COMMANDS[f"volume_{args.volume}"])

    elif args.name:
        set_speaker_name(mac, args.name)

    elif args.raw:
        raw_bytes = bytes.fromhex(args.raw.replace(" ", ""))
        send_spp_command(mac, raw_bytes)

    elif args.interactive:
        interactive_mode(mac)

    else:
        parser.print_help()

"""SPP (RFCOMM) transport for UE Mini Boom — Classic Bluetooth."""

import socket
import subprocess
import time

from .protocol import SPP_UUID, UECommand, build_spp_command

# Default RFCOMM channel for the LWACP service on UE speakers.
_DEFAULT_RFCOMM_CHANNEL = 5


def _find_rfcomm_channel(mac_address: str) -> int | None:
    """Discover the RFCOMM channel for the SPP service via sdptool.

    Returns the channel number or None if lookup fails.
    """
    try:
        result = subprocess.run(
            ["sdptool", "search", "--bdaddr", mac_address, "SP"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if line.startswith("Channel:"):
                return int(line.split(":")[1].strip())
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass
    return None


def send_spp_command(mac_address: str, command: bytes, verbose: bool = True):
    """
    Send a command to the UE Mini Boom over Bluetooth SPP (RFCOMM).

    Uses Python's native AF_BLUETOOTH socket (Linux kernel support).
    Falls back to pybluez if native sockets are unavailable.
    """
    if not hasattr(socket, "AF_BLUETOOTH"):
        # Fallback: try pybluez
        return _send_spp_pybluez(mac_address, command, verbose)

    channel = _find_rfcomm_channel(mac_address)
    if channel is None:
        if verbose:
            print(f"sdptool lookup failed, using default channel {_DEFAULT_RFCOMM_CHANNEL}")
        channel = _DEFAULT_RFCOMM_CHANNEL

    if verbose:
        print(f"Connecting to {mac_address} on RFCOMM channel {channel}...")

    sock = None
    try:
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.connect((mac_address, channel))

        if verbose:
            hex_str = " ".join(f"{b:02X}" for b in command)
            print(f"Sending: {hex_str}")

        sock.send(command)
        time.sleep(0.3)

        try:
            sock.settimeout(1.0)
            response = sock.recv(1024)
            if verbose and response:
                hex_resp = " ".join(f"{b:02X}" for b in response)
                print(f"Response: {hex_resp}")
        except (TimeoutError, OSError):
            pass

        if verbose:
            print("Command sent successfully.")
        return True

    except Exception as e:
        print(f"ERROR: Could not connect — {e}")
        return False
    finally:
        if sock is not None:
            sock.close()


def _send_spp_pybluez(mac_address: str, command: bytes, verbose: bool = True):
    """Fallback SPP transport using pybluez (non-Linux or missing AF_BLUETOOTH)."""
    try:
        from bluetooth import RFCOMM, BluetoothSocket, find_service
    except ImportError:
        print("ERROR: No Bluetooth SPP transport available.")
        print("       On Linux, upgrade to Python 3.3+ (AF_BLUETOOTH built-in).")
        print("       On other platforms: pip install pybluez")
        return False

    if verbose:
        print(f"Searching for SPP service on {mac_address}...")

    service_matches = find_service(uuid=SPP_UUID, address=mac_address)

    if not service_matches:
        print(f"ERROR: No SPP service found on {mac_address}")
        print("       Make sure the speaker is paired and connected.")
        return False

    match = service_matches[0]
    if verbose:
        print(f"Found service: {match['name']} on port {match['port']}")

    sock = None
    try:
        sock = BluetoothSocket(RFCOMM)
        sock.connect((match["host"], match["port"]))

        if verbose:
            hex_str = " ".join(f"{b:02X}" for b in command)
            print(f"Sending: {hex_str}")

        sock.send(command)
        time.sleep(0.3)

        try:
            sock.settimeout(1.0)
            response = sock.recv(1024)
            if verbose and response:
                hex_resp = " ".join(f"{b:02X}" for b in response)
                print(f"Response: {hex_resp}")
        except Exception:
            pass

        if verbose:
            print("Command sent successfully.")
        return True

    except Exception as e:
        print(f"ERROR: Could not connect — {e}")
        return False
    finally:
        if sock is not None:
            sock.close()


def query_spp_value(mac_address: str, command_id: int) -> int | None:
    """Query the current value of a command from the speaker via LWACP.

    Sends a parameterless command and parses the response.
    Response format: [len] [00] [00] [01] [cmd_id] [value]

    Returns the value byte or None on failure.
    """
    if not hasattr(socket, "AF_BLUETOOTH"):
        return None

    channel = _find_rfcomm_channel(mac_address)
    if channel is None:
        channel = _DEFAULT_RFCOMM_CHANNEL

    query = bytes([0x02, 0x01, command_id])
    sock = None
    try:
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.connect((mac_address, channel))
        time.sleep(0.3)
        sock.send(query)
        time.sleep(0.5)
        sock.settimeout(2.0)
        resp = sock.recv(1024)
        # Parse: look for cmd_id in response followed by value byte
        for i in range(len(resp) - 1):
            if resp[i] == command_id:
                return resp[i + 1]
    except Exception:
        pass
    finally:
        if sock is not None:
            sock.close()
    return None


def query_spp_values(mac_address: str, command_ids: list[int]) -> dict[int, int | None]:
    """Query multiple LWACP values in a single RFCOMM connection.

    Sends each command with a delay between them to avoid overwhelming the speaker.
    Returns a dict mapping command_id -> value (or None on failure).
    """
    results = {cid: None for cid in command_ids}

    if not hasattr(socket, "AF_BLUETOOTH") or not command_ids:
        return results

    channel = _find_rfcomm_channel(mac_address)
    if channel is None:
        channel = _DEFAULT_RFCOMM_CHANNEL

    sock = None
    try:
        sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        sock.connect((mac_address, channel))
        time.sleep(0.3)

        for command_id in command_ids:
            query = bytes([0x02, 0x01, command_id])
            sock.send(query)
            time.sleep(1.0)  # 1s delay between queries — safe pacing
            try:
                sock.settimeout(2.0)
                resp = sock.recv(1024)
                for i in range(len(resp) - 1):
                    if resp[i] == command_id:
                        results[command_id] = resp[i + 1]
                        break
            except (TimeoutError, OSError):
                pass
    except Exception:
        pass
    finally:
        if sock is not None:
            sock.close()
    return results


def set_speaker_name(mac_address: str, name: str):
    """Set the speaker's display name via SPP."""
    name_bytes = name.encode("utf-8")[:32]  # Max 32 bytes
    cmd = build_spp_command(UECommand.SET_NAME, *name_bytes)
    return send_spp_command(mac_address, cmd)

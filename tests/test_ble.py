"""Tests for BlueZ D-Bus transport and device discovery."""

from unittest.mock import MagicMock, patch

from ue_mini_boom_controller.ble import (
    get_battery,
    get_device_status,
    get_paired_ue_devices,
    is_ue_device,
)

# --- get_device_status tests ---


def test_get_device_status_connected():
    """Should parse all fields from bluetoothctl info output."""
    mock_result = MagicMock()
    mock_result.stdout = (
        "Device 88:C6:26:20:33:40 (public)\n"
        "\tName: JoretapoL\n"
        "\tPaired: yes\n"
        "\tConnected: yes\n"
        "\tBattery Percentage: 0x64 (100)\n"
    )

    with patch("ue_mini_boom_controller.ble.subprocess.run", return_value=mock_result):
        status = get_device_status("88:C6:26:20:33:40")

    assert status["name"] == "JoretapoL"
    assert status["connected"] is True
    assert status["paired"] is True
    assert status["battery"] == 100


def test_get_device_status_disconnected():
    """Should report connected=False for disconnected device."""
    mock_result = MagicMock()
    mock_result.stdout = (
        "Device 88:C6:26:20:33:40 (public)\n\tName: JoretapoL\n\tPaired: yes\n\tConnected: no\n"
    )

    with patch("ue_mini_boom_controller.ble.subprocess.run", return_value=mock_result):
        status = get_device_status("88:C6:26:20:33:40")

    assert status["connected"] is False
    assert "battery" not in status


def test_get_device_status_bluetoothctl_missing():
    """Should return empty dict when bluetoothctl is not installed."""
    with patch("ue_mini_boom_controller.ble.subprocess.run", side_effect=FileNotFoundError):
        status = get_device_status("88:C6:26:20:33:40")

    assert status == {}


# --- get_battery tests ---


def test_get_battery_success():
    """Should parse battery percentage from dbus-send output."""
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = (
        "method return time=1234 sender=:1.5 -> destination=:1.99 serial=42 reply_serial=2\n"
        "   variant       byte 100\n"
    )

    with patch("ue_mini_boom_controller.ble.subprocess.run", return_value=mock_result):
        result = get_battery("88:C6:26:20:33:40")

    assert result == 100


def test_get_battery_no_battery_interface():
    """Should return -1 when Battery1 interface is not available."""
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stdout = ""

    with patch("ue_mini_boom_controller.ble.subprocess.run", return_value=mock_result):
        result = get_battery("88:C6:26:20:33:40")

    assert result == -1


def test_get_battery_dbus_missing():
    """Should return -1 when dbus-send is not installed."""
    with patch("ue_mini_boom_controller.ble.subprocess.run", side_effect=FileNotFoundError):
        result = get_battery("88:C6:26:20:33:40")

    assert result == -1


# --- is_ue_device tests ---


def test_is_ue_device_name_keyword():
    """Device with UE keyword in name should match."""
    assert is_ue_device("FF:EE:DD:CC:BB:AA", "UE MINI BOOM") is True


def test_is_ue_device_oui_prefix():
    """Device with known OUI prefix should match even with custom name."""
    assert is_ue_device("88:C6:26:AA:BB:CC", "RenamedSpeaker") is True


def test_is_ue_device_no_match():
    """Device with unknown OUI and no UE keywords should not match."""
    assert is_ue_device("FF:EE:DD:CC:BB:AA", "Some Headphones") is False


# --- get_paired_ue_devices tests ---


def test_get_paired_ue_devices_filters():
    """Should return only UE devices from bluetoothctl output."""
    stdout = (
        "Device 88:C6:26:AA:BB:CC SpeakerRight\n"
        "Device 88:C6:26:DD:EE:FF SpeakerLeft\n"
        "Device FF:EE:DD:CC:BB:AA Some Headphones\n"
    )
    mock_result = MagicMock()
    mock_result.stdout = stdout

    with patch("ue_mini_boom_controller.ble.subprocess.run", return_value=mock_result):
        devices = get_paired_ue_devices()

    assert len(devices) == 2
    assert devices[0] == ("88:C6:26:AA:BB:CC", "SpeakerRight")
    assert devices[1] == ("88:C6:26:DD:EE:FF", "SpeakerLeft")


def test_get_paired_ue_devices_none_found():
    """Should return empty list when no UE devices are paired."""
    mock_result = MagicMock()
    mock_result.stdout = "Device FF:EE:DD:CC:BB:AA Some Headphones\n"

    with patch("ue_mini_boom_controller.ble.subprocess.run", return_value=mock_result):
        devices = get_paired_ue_devices()

    assert devices == []


def test_get_paired_ue_devices_bluetoothctl_missing():
    """Should return empty list when bluetoothctl is not installed."""
    with patch("ue_mini_boom_controller.ble.subprocess.run", side_effect=FileNotFoundError):
        devices = get_paired_ue_devices()

    assert devices == []

"""Tests for SPP transport (mock-based)."""

import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

from ue_mini_boom_controller.protocol import COMMANDS, UECommand, build_spp_command
from ue_mini_boom_controller.spp import send_spp_command, set_speaker_name

_TEST_CMD = COMMANDS["battery_announce"]


def _make_bluetooth_mock():
    """Create a mock bluetooth module with BluetoothSocket, RFCOMM, find_service."""
    bt = ModuleType("bluetooth")
    bt.BluetoothSocket = MagicMock
    bt.RFCOMM = 3
    bt.find_service = MagicMock()
    return bt


class TestSendSppNative:
    """Tests for the native AF_BLUETOOTH socket path."""

    def _mock_native_socket(self):
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = TimeoutError
        return mock_sock

    def test_success(self):
        mock_sock = self._mock_native_socket()
        mock_sdp = MagicMock()
        mock_sdp.stdout = "  Channel: 5\n"
        mock_sdp.returncode = 0

        with (
            patch("ue_mini_boom_controller.spp.socket") as mock_socket_mod,
            patch("ue_mini_boom_controller.spp.subprocess.run", return_value=mock_sdp),
        ):
            mock_socket_mod.AF_BLUETOOTH = 31
            mock_socket_mod.SOCK_STREAM = 1
            mock_socket_mod.BTPROTO_RFCOMM = 3
            mock_socket_mod.socket.return_value = mock_sock

            result = send_spp_command("AA:BB:CC:DD:EE:FF", _TEST_CMD, verbose=False)

        assert result is True
        mock_sock.connect.assert_called_once_with(("AA:BB:CC:DD:EE:FF", 5))
        mock_sock.send.assert_called_once_with(_TEST_CMD)
        mock_sock.close.assert_called_once()

    def test_connection_error(self):
        mock_sock = self._mock_native_socket()
        mock_sock.connect.side_effect = ConnectionRefusedError("Connection refused")
        mock_sdp = MagicMock()
        mock_sdp.stdout = "  Channel: 5\n"
        mock_sdp.returncode = 0

        with (
            patch("ue_mini_boom_controller.spp.socket") as mock_socket_mod,
            patch("ue_mini_boom_controller.spp.subprocess.run", return_value=mock_sdp),
        ):
            mock_socket_mod.AF_BLUETOOTH = 31
            mock_socket_mod.SOCK_STREAM = 1
            mock_socket_mod.BTPROTO_RFCOMM = 3
            mock_socket_mod.socket.return_value = mock_sock

            result = send_spp_command("AA:BB:CC:DD:EE:FF", _TEST_CMD, verbose=False)

        assert result is False

    def test_sdptool_failure_uses_default_channel(self):
        mock_sock = self._mock_native_socket()

        with (
            patch("ue_mini_boom_controller.spp.socket") as mock_socket_mod,
            patch(
                "ue_mini_boom_controller.spp.subprocess.run",
                side_effect=FileNotFoundError,
            ),
        ):
            mock_socket_mod.AF_BLUETOOTH = 31
            mock_socket_mod.SOCK_STREAM = 1
            mock_socket_mod.BTPROTO_RFCOMM = 3
            mock_socket_mod.socket.return_value = mock_sock

            result = send_spp_command("AA:BB:CC:DD:EE:FF", _TEST_CMD, verbose=False)

        assert result is True
        mock_sock.connect.assert_called_once_with(("AA:BB:CC:DD:EE:FF", 5))


class TestSendSppPybluezFallback:
    """Tests for the pybluez fallback path (no AF_BLUETOOTH)."""

    def test_success(self):
        bt = _make_bluetooth_mock()
        mock_socket = MagicMock()
        mock_socket.recv.return_value = b""
        bt.BluetoothSocket = MagicMock(return_value=mock_socket)
        bt.find_service.return_value = [{"host": "AA:BB:CC:DD:EE:FF", "port": 1, "name": "LWACP"}]

        with (
            patch("ue_mini_boom_controller.spp.socket") as mock_socket_mod,
            patch.dict(sys.modules, {"bluetooth": bt}),
        ):
            del mock_socket_mod.AF_BLUETOOTH  # Force pybluez fallback
            result = send_spp_command("AA:BB:CC:DD:EE:FF", _TEST_CMD, verbose=False)

        assert result is True
        mock_socket.connect.assert_called_once_with(("AA:BB:CC:DD:EE:FF", 1))
        mock_socket.send.assert_called_once_with(_TEST_CMD)
        mock_socket.close.assert_called_once()

    def test_no_service(self):
        bt = _make_bluetooth_mock()
        bt.find_service.return_value = []

        with (
            patch("ue_mini_boom_controller.spp.socket") as mock_socket_mod,
            patch.dict(sys.modules, {"bluetooth": bt}),
        ):
            del mock_socket_mod.AF_BLUETOOTH
            result = send_spp_command("AA:BB:CC:DD:EE:FF", _TEST_CMD, verbose=False)

        assert result is False

    def test_pybluez_missing(self):
        with (
            patch("ue_mini_boom_controller.spp.socket") as mock_socket_mod,
            patch.dict(sys.modules, {"bluetooth": None}),
        ):
            del mock_socket_mod.AF_BLUETOOTH
            result = send_spp_command("AA:BB:CC:DD:EE:FF", _TEST_CMD, verbose=False)

        assert result is False


class TestSetSpeakerName:
    def test_encoding(self):
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = TimeoutError
        mock_sdp = MagicMock()
        mock_sdp.stdout = "  Channel: 5\n"
        mock_sdp.returncode = 0

        with (
            patch("ue_mini_boom_controller.spp.socket") as mock_socket_mod,
            patch("ue_mini_boom_controller.spp.subprocess.run", return_value=mock_sdp),
        ):
            mock_socket_mod.AF_BLUETOOTH = 31
            mock_socket_mod.SOCK_STREAM = 1
            mock_socket_mod.BTPROTO_RFCOMM = 3
            mock_socket_mod.socket.return_value = mock_sock

            set_speaker_name("AA:BB:CC:DD:EE:FF", "MyBoom")

        sent_cmd = mock_sock.send.call_args[0][0]
        name_bytes = "MyBoom".encode("utf-8")
        expected = build_spp_command(UECommand.SET_NAME, *name_bytes)
        assert sent_cmd == expected

    def test_truncation(self):
        mock_sock = MagicMock()
        mock_sock.recv.side_effect = TimeoutError
        mock_sdp = MagicMock()
        mock_sdp.stdout = "  Channel: 5\n"
        mock_sdp.returncode = 0

        with (
            patch("ue_mini_boom_controller.spp.socket") as mock_socket_mod,
            patch("ue_mini_boom_controller.spp.subprocess.run", return_value=mock_sdp),
        ):
            mock_socket_mod.AF_BLUETOOTH = 31
            mock_socket_mod.SOCK_STREAM = 1
            mock_socket_mod.BTPROTO_RFCOMM = 3
            mock_socket_mod.socket.return_value = mock_sock

            long_name = "A" * 50
            set_speaker_name("AA:BB:CC:DD:EE:FF", long_name)

        sent_cmd = mock_sock.send.call_args[0][0]
        truncated_bytes = long_name.encode("utf-8")[:32]
        expected = build_spp_command(UECommand.SET_NAME, *truncated_bytes)
        assert sent_cmd == expected

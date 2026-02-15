"""Tests for CLI argument parsing and dispatch."""

import sys
from unittest.mock import patch

import pytest

from ue_mini_boom_controller.cli import main
from ue_mini_boom_controller.protocol import COMMANDS


class TestCLIHelp:
    def test_help_exits_zero(self, capsys):
        with pytest.raises(SystemExit) as exc_info:
            with patch.object(sys, "argv", ["ueboom", "--help"]):
                main()
        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "UE Mini Boom Controller" in captured.out
        assert "--mac" in captured.out
        assert "--list" in captured.out
        assert "--battery" in captured.out
        assert "--eq" in captured.out
        assert "--stereo" in captured.out
        assert "--interactive" in captured.out
        assert "--raw" in captured.out

    def test_no_args_prints_help(self, capsys):
        with patch.object(sys, "argv", ["ueboom"]):
            with patch(
                "ue_mini_boom_controller.cli.get_paired_ue_devices", return_value=[]
            ):
                main()
        captured = capsys.readouterr()
        assert "--mac" in captured.out


class TestCLIArgumentParsing:
    def test_mac_required_for_eq(self, capsys):
        """--eq without --mac should print help when no devices found."""
        with patch.object(sys, "argv", ["ueboom", "--eq", "outloud"]):
            with patch(
                "ue_mini_boom_controller.cli.get_paired_ue_devices", return_value=[]
            ):
                main()
        captured = capsys.readouterr()
        assert "--mac" in captured.out



class TestCLIAutoDetect:
    def test_auto_detect_single_device(self, capsys):
        """Single paired UE device should be auto-detected."""
        with patch.object(sys, "argv", ["ueboom", "--battery"]):
            with patch(
                "ue_mini_boom_controller.cli.get_paired_ue_devices",
                return_value=[("88:C6:26:AA:BB:CC", "SpeakerRight")],
            ):
                with patch(
                    "ue_mini_boom_controller.cli.get_battery", return_value=75
                ):
                    main()
        captured = capsys.readouterr()
        assert "Auto-detected: SpeakerRight (88:C6:26:AA:BB:CC)" in captured.out
        assert "Battery: 75%" in captured.out

    def test_auto_detect_multiple_devices(self, capsys):
        """Multiple paired UE devices should prompt user to specify --mac."""
        with patch.object(sys, "argv", ["ueboom", "--battery"]):
            with patch(
                "ue_mini_boom_controller.cli.get_paired_ue_devices",
                return_value=[
                    ("88:C6:26:AA:BB:CC", "SpeakerRight"),
                    ("88:C6:26:DD:EE:FF", "SpeakerLeft"),
                ],
            ):
                main()
        captured = capsys.readouterr()
        assert "Multiple UE speakers found" in captured.out
        assert "SpeakerRight" in captured.out
        assert "SpeakerLeft" in captured.out

    def test_auto_detect_no_devices(self, capsys):
        """No paired UE devices should print help."""
        with patch.object(sys, "argv", ["ueboom", "--battery"]):
            with patch(
                "ue_mini_boom_controller.cli.get_paired_ue_devices", return_value=[]
            ):
                main()
        captured = capsys.readouterr()
        assert "--mac" in captured.out


class TestCLIList:
    def test_list_shows_devices(self, capsys):
        """--list should show paired UE speakers."""
        with patch.object(sys, "argv", ["ueboom", "--list"]):
            with patch(
                "ue_mini_boom_controller.cli.get_paired_ue_devices",
                return_value=[
                    ("88:C6:26:AA:BB:CC", "SpeakerRight"),
                    ("88:C6:26:DD:EE:FF", "SpeakerLeft"),
                ],
            ):
                main()
        captured = capsys.readouterr()
        assert "2 paired UE speaker(s)" in captured.out
        assert "SpeakerRight" in captured.out
        assert "SpeakerLeft" in captured.out

    def test_list_no_devices(self, capsys):
        """--list with no paired UE speakers should show pairing instructions."""
        with patch.object(sys, "argv", ["ueboom", "--list"]):
            with patch(
                "ue_mini_boom_controller.cli.get_paired_ue_devices", return_value=[]
            ):
                main()
        captured = capsys.readouterr()
        assert "No paired UE speakers found" in captured.out
        assert "bluetoothctl pair" in captured.out


_STEREO_SETUP_ARGV = ["ueboom", "--mac", "AA:BB:CC:DD:EE:FF", "--stereo-setup"]


class TestCLIStereoSetup:
    def test_stereo_setup_happy_path_default_left(self, capsys):
        """Stereo setup with default left role (Enter at both prompts)."""
        with patch.object(sys, "argv", _STEREO_SETUP_ARGV):
            with patch(
                "ue_mini_boom_controller.cli.send_spp_command", return_value=True
            ) as mock_spp:
                with patch("builtins.input", side_effect=["y", "", ""]):
                    with patch("ue_mini_boom_controller.cli.time.sleep"):
                        main()
        captured = capsys.readouterr()
        assert "Stereo Setup" in captured.out
        assert "discovery mode" in captured.out
        assert "Stereo setup complete" in captured.out
        assert mock_spp.call_count == 2
        mock_spp.assert_any_call(
            "AA:BB:CC:DD:EE:FF", COMMANDS["mode_stereo"], verbose=False
        )
        mock_spp.assert_any_call(
            "AA:BB:CC:DD:EE:FF", COMMANDS["role_left"], verbose=False
        )

    def test_stereo_setup_right_channel(self, capsys):
        """Stereo setup with right channel selected."""
        with patch.object(sys, "argv", _STEREO_SETUP_ARGV):
            with patch(
                "ue_mini_boom_controller.cli.send_spp_command", return_value=True
            ) as mock_spp:
                with patch("builtins.input", side_effect=["y", "", "r"]):
                    with patch("ue_mini_boom_controller.cli.time.sleep"):
                        main()
        captured = capsys.readouterr()
        assert "Stereo setup complete" in captured.out
        mock_spp.assert_any_call(
            "AA:BB:CC:DD:EE:FF", COMMANDS["role_right"], verbose=False
        )

    def test_stereo_setup_send_failure(self, capsys):
        """Stereo setup aborts when initial mode_stereo command fails."""
        with patch.object(sys, "argv", _STEREO_SETUP_ARGV):
            with patch(
                "ue_mini_boom_controller.cli.send_spp_command", return_value=False
            ) as mock_spp:
                with patch("builtins.input", side_effect=["y"]):
                    main()
        captured = capsys.readouterr()
        assert "ERROR" in captured.out
        assert mock_spp.call_count == 1

    def test_stereo_setup_role_failure(self, capsys):
        """Stereo setup aborts when role assignment command fails."""
        with patch.object(sys, "argv", _STEREO_SETUP_ARGV):
            with patch(
                "ue_mini_boom_controller.cli.send_spp_command",
                side_effect=[True, False],
            ) as mock_spp:
                with patch("builtins.input", side_effect=["y", "", ""]):
                    with patch("ue_mini_boom_controller.cli.time.sleep"):
                        main()
        captured = capsys.readouterr()
        assert "Failed to assign stereo role" in captured.out
        assert mock_spp.call_count == 2

    def test_stereo_setup_garbage_input_defaults_left(self, capsys):
        """Unrecognized role input warns and defaults to left channel."""
        with patch.object(sys, "argv", _STEREO_SETUP_ARGV):
            with patch(
                "ue_mini_boom_controller.cli.send_spp_command", return_value=True
            ) as mock_spp:
                with patch("builtins.input", side_effect=["y", "", "banana"]):
                    with patch("ue_mini_boom_controller.cli.time.sleep"):
                        main()
        captured = capsys.readouterr()
        assert "Unrecognized" in captured.out
        assert "left" in captured.out
        mock_spp.assert_any_call(
            "AA:BB:CC:DD:EE:FF", COMMANDS["role_left"], verbose=False
        )

    def test_stereo_setup_keyboard_interrupt(self, capsys):
        """Ctrl+C after stereo sent prints cancellation and discovery warning."""
        with patch.object(sys, "argv", _STEREO_SETUP_ARGV):
            with patch(
                "ue_mini_boom_controller.cli.send_spp_command", return_value=True
            ) as mock_spp:
                with patch("builtins.input", side_effect=["y", KeyboardInterrupt]):
                    main()
        captured = capsys.readouterr()
        assert "cancelled" in captured.out.lower()
        assert "discovery mode" in captured.out.lower()
        assert mock_spp.call_count == 1

    def test_stereo_setup_eof_error(self, capsys):
        """EOFError (piped/closed stdin) prints cancellation message."""
        with patch.object(sys, "argv", _STEREO_SETUP_ARGV):
            with patch(
                "ue_mini_boom_controller.cli.send_spp_command", return_value=True
            ) as mock_spp:
                with patch("builtins.input", side_effect=["y", EOFError]):
                    main()
        captured = capsys.readouterr()
        assert "cancelled" in captured.out.lower()
        assert mock_spp.call_count == 1

    def test_stereo_setup_declined(self, capsys):
        """Declining the confirmation prompt cancels without sending commands."""
        with patch.object(sys, "argv", _STEREO_SETUP_ARGV):
            with patch(
                "ue_mini_boom_controller.cli.send_spp_command", return_value=True
            ) as mock_spp:
                with patch("builtins.input", return_value="n"):
                    main()
        captured = capsys.readouterr()
        assert "cancelled" in captured.out.lower()
        assert mock_spp.call_count == 0

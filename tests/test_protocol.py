"""Tests for protocol constants and command builder."""

from ue_mini_boom_controller.protocol import (
    BLE_ALARM_UUID,
    BLE_BATTERY_UUID,
    BLE_COLOR_UUID,
    BLE_FW_VERSION_UUID,
    BLE_NAME_UUID,
    BLE_POWER_UUID,
    BLE_SERIAL_UUID,
    BLE_SERVICE_UUID,
    COMMANDS,
    SPP_UUID,
    UECommand,
    build_spp_command,
)


class TestBuildSppCommand:
    def test_basic(self):
        """build_spp_command(0x64, 0x01) -> [0x03, 0x01, 0x64, 0x01]"""
        result = build_spp_command(0x64, 0x01)
        assert result == bytes([0x03, 0x01, 0x64, 0x01])

    def test_no_params(self):
        """build_spp_command(0x6B) -> [0x02, 0x01, 0x6B] (battery announce)"""
        result = build_spp_command(0x6B)
        assert result == bytes([0x02, 0x01, 0x6B])

    def test_multiple_params(self):
        """build_spp_command(0xBB, 0x01, 0x01) -> [0x04, 0x01, 0xBB, 0x01, 0x01]"""
        result = build_spp_command(0xBB, 0x01, 0x01)
        assert result == bytes([0x04, 0x01, 0xBB, 0x01, 0x01])


class TestUECommandConstants:
    def test_eq_preset(self):
        assert UECommand.EQ_PRESET == 0x64

    def test_sonification(self):
        assert UECommand.SONIFICATION == 0x65

    def test_double_up_mode(self):
        assert UECommand.DOUBLE_UP_MODE == 0x67

    def test_double_up_role(self):
        assert UECommand.DOUBLE_UP_ROLE == 0x68

    def test_double_up_lock(self):
        assert UECommand.DOUBLE_UP_LOCK == 0x69

    def test_battery_announce(self):
        assert UECommand.BATTERY_ANNOUNCE == 0x6B

    def test_emit_sound(self):
        assert UECommand.EMIT_SOUND == 0x6C

    def test_set_name(self):
        assert UECommand.SET_NAME == 0x72

    def test_ble_state(self):
        assert UECommand.BLE_STATE == 0xB9

    def test_volume_adjust(self):
        assert UECommand.VOLUME_ADJUST == 0xBB


class TestCommandsDict:
    def test_completeness(self):
        """COMMANDS dict has all 5 expected keys."""
        expected_keys = {
            "battery_announce",
            "sound_power_on",
            "stereo_discover",
            "role_left",
            "role_right",
        }
        assert set(COMMANDS.keys()) == expected_keys

    def test_all_values_are_bytes(self):
        for key, value in COMMANDS.items():
            assert isinstance(value, bytes), f"COMMANDS['{key}'] is not bytes"

    def test_role_left_value(self):
        assert COMMANDS["role_left"] == build_spp_command(0x68, 0x00)

    def test_role_right_value(self):
        assert COMMANDS["role_right"] == build_spp_command(0x68, 0x01)

    def test_battery_announce_value(self):
        assert COMMANDS["battery_announce"] == build_spp_command(0x6B)


class TestUUIDConstants:
    def test_spp_uuid_format(self):
        assert isinstance(SPP_UUID, str)
        assert len(SPP_UUID) > 0
        # UUID format: 8-4-4-4-12
        parts = SPP_UUID.split("-")
        assert len(parts) == 5

    def test_ble_uuids_are_strings(self):
        for uuid in [
            BLE_SERVICE_UUID,
            BLE_POWER_UUID,
            BLE_BATTERY_UUID,
            BLE_NAME_UUID,
            BLE_FW_VERSION_UUID,
            BLE_SERIAL_UUID,
            BLE_COLOR_UUID,
            BLE_ALARM_UUID,
        ]:
            assert isinstance(uuid, str)
            assert len(uuid) > 0

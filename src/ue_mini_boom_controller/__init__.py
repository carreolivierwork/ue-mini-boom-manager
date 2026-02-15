"""UE Mini Boom Controller — replaces the official app."""

from importlib.metadata import version

__version__ = version("ue-mini-boom-controller")

from ue_mini_boom_controller.protocol import COMMANDS, UECommand, build_spp_command

__all__ = ["UECommand", "build_spp_command", "COMMANDS"]

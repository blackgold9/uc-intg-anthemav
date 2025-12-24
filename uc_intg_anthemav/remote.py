"""
Anthem Remote Entity - Working version with proper send_cmd handling.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.remote import Commands, Features, Options, Remote

from .config import AnthemDeviceConfig, ZoneConfig
from .device import AnthemDevice

_LOG = logging.getLogger(__name__)


class AnthemRemote(Remote):
    LISTENING_MODES = {
        "None": 0,
        "AnthemLogic Cinema": 1,
        "AnthemLogic Music": 2,
        "Dolby Surround": 3,
        "DTS Neural:X": 4,
        "Stereo": 5,
        "Multi-Channel Stereo": 6,
        "All-Channel Stereo": 7,
        "PLIIx Movie": 8,
        "PLIIx Music": 9,
        "Neo:6 Cinema": 10,
        "Neo:6 Music": 11,
        "Dolby Digital": 12,
        "DTS": 13,
        "PCM Stereo": 14,
        "Direct": 15,
    }

    def __init__(
        self,
        device_config: AnthemDeviceConfig,
        device: AnthemDevice,
        zone_config: ZoneConfig,
    ):
        """Initialize remote entity with UI pages."""
        self._device = device
        self._device_config = device_config
        self._zone_config = zone_config

        # Create entity ID
        if zone_config.zone_number == 1:
            entity_id = f"remote.{device_config.identifier}"
            entity_name = f"{device_config.name} Audio Controls"
        else:
            entity_id = (
                f"remote.{device_config.identifier}.zone{zone_config.zone_number}"
            )
            entity_name = (
                f"{device_config.name} Zone {zone_config.zone_number} Audio Controls"
            )

        # Features - Only SEND_CMD (no power control)
        features = [Features.SEND_CMD]

        # No STATE attribute needed for remote entities without on_off
        attributes = {}

        # Initialize base class WITHOUT options
        super().__init__(
            entity_id,
            entity_name,
            features,
            attributes,
            cmd_handler=self.handle_command,
        )

        # Define ALL simple commands
        simple_commands = [
            # Listening Modes
            "DOLBY_SURROUND",
            "DTS_NEURAL_X",
            "ANTHEMLOGIC_CINEMA",
            "ANTHEMLOGIC_MUSIC",
            "STEREO",
            "MULTI_CHANNEL_STEREO",
            "DIRECT",
            "PLIIX_MOVIE",
            "PLIIX_MUSIC",
            "NEO6_CINEMA",
            "NEO6_MUSIC",
            # Audio Mode Navigation
            "AUDIO_MODE_UP",
            "AUDIO_MODE_DOWN",
            # Tone Controls
            "BASS_UP",
            "BASS_DOWN",
            "TREBLE_UP",
            "TREBLE_DOWN",
            # Balance
            "BALANCE_LEFT",
            "BALANCE_RIGHT",
            # Dolby Settings
            "DOLBY_DRC_NORMAL",
            "DOLBY_DRC_REDUCED",
            "DOLBY_DRC_LATE_NIGHT",
            "DOLBY_CENTER_SPREAD_ON",
            "DOLBY_CENTER_SPREAD_OFF",
        ]

        # Define UI with pages
        user_interface = {
            "pages": [
                {
                    "page_id": "audio_modes",
                    "name": "Audio Modes",
                    "grid": {"width": 4, "height": 6},
                    "items": [
                        # Row 1: Main Modes
                        {
                            "type": "text",
                            "text": "Dolby\nSurround",
                            "command": {"cmd_id": "DOLBY_SURROUND"},
                            "location": {"x": 0, "y": 0},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "DTS\nNeural:X",
                            "command": {"cmd_id": "DTS_NEURAL_X"},
                            "location": {"x": 2, "y": 0},
                            "size": {"width": 2, "height": 1},
                        },
                        # Row 2: AnthemLogic
                        {
                            "type": "text",
                            "text": "AnthemLogic\nCinema",
                            "command": {"cmd_id": "ANTHEMLOGIC_CINEMA"},
                            "location": {"x": 0, "y": 1},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "AnthemLogic\nMusic",
                            "command": {"cmd_id": "ANTHEMLOGIC_MUSIC"},
                            "location": {"x": 2, "y": 1},
                            "size": {"width": 2, "height": 1},
                        },
                        # Row 3: Stereo Modes
                        {
                            "type": "text",
                            "text": "Stereo",
                            "command": {"cmd_id": "STEREO"},
                            "location": {"x": 0, "y": 2},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Multi-Ch\nStereo",
                            "command": {"cmd_id": "MULTI_CHANNEL_STEREO"},
                            "location": {"x": 2, "y": 2},
                            "size": {"width": 2, "height": 1},
                        },
                        # Row 4: Direct + Mode Navigation
                        {
                            "type": "text",
                            "text": "Direct",
                            "command": {"cmd_id": "DIRECT"},
                            "location": {"x": 0, "y": 3},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:up-arrow",
                            "command": {"cmd_id": "AUDIO_MODE_UP"},
                            "location": {"x": 2, "y": 3},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:down-arrow",
                            "command": {"cmd_id": "AUDIO_MODE_DOWN"},
                            "location": {"x": 3, "y": 3},
                        },
                    ],
                },
                {
                    "page_id": "tone_control",
                    "name": "Tone Control",
                    "grid": {"width": 4, "height": 6},
                    "items": [
                        # Bass Controls
                        {
                            "type": "text",
                            "text": "Bass",
                            "location": {"x": 0, "y": 0},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:up-arrow",
                            "command": {"cmd_id": "BASS_UP"},
                            "location": {"x": 2, "y": 0},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:down-arrow",
                            "command": {"cmd_id": "BASS_DOWN"},
                            "location": {"x": 3, "y": 0},
                        },
                        # Treble Controls
                        {
                            "type": "text",
                            "text": "Treble",
                            "location": {"x": 0, "y": 1},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:up-arrow",
                            "command": {"cmd_id": "TREBLE_UP"},
                            "location": {"x": 2, "y": 1},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:down-arrow",
                            "command": {"cmd_id": "TREBLE_DOWN"},
                            "location": {"x": 3, "y": 1},
                        },
                        # Balance Controls
                        {
                            "type": "text",
                            "text": "Balance",
                            "location": {"x": 0, "y": 2},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:left-arrow",
                            "command": {"cmd_id": "BALANCE_LEFT"},
                            "location": {"x": 2, "y": 2},
                        },
                        {
                            "type": "icon",
                            "icon": "uc:right-arrow",
                            "command": {"cmd_id": "BALANCE_RIGHT"},
                            "location": {"x": 3, "y": 2},
                        },
                    ],
                },
                {
                    "page_id": "dolby_settings",
                    "name": "Dolby Settings",
                    "grid": {"width": 4, "height": 6},
                    "items": [
                        # Dynamic Range
                        {
                            "type": "text",
                            "text": "DRC\nNormal",
                            "command": {"cmd_id": "DOLBY_DRC_NORMAL"},
                            "location": {"x": 0, "y": 0},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "DRC\nReduced",
                            "command": {"cmd_id": "DOLBY_DRC_REDUCED"},
                            "location": {"x": 2, "y": 0},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "DRC\nLate Night",
                            "command": {"cmd_id": "DOLBY_DRC_LATE_NIGHT"},
                            "location": {"x": 0, "y": 1},
                            "size": {"width": 2, "height": 1},
                        },
                        # Center Spread
                        {
                            "type": "text",
                            "text": "Center\nSpread ON",
                            "command": {"cmd_id": "DOLBY_CENTER_SPREAD_ON"},
                            "location": {"x": 0, "y": 2},
                            "size": {"width": 2, "height": 1},
                        },
                        {
                            "type": "text",
                            "text": "Center\nSpread OFF",
                            "command": {"cmd_id": "DOLBY_CENTER_SPREAD_OFF"},
                            "location": {"x": 2, "y": 2},
                            "size": {"width": 2, "height": 1},
                        },
                    ],
                },
            ]
        }

        # Set options as property AFTER initialization
        self.options = {
            Options.SIMPLE_COMMANDS: simple_commands,
            "user_interface": user_interface,
        }

        _LOG.info(
            "[%s] Remote entity initialized with %d commands and 3 UI pages",
            entity_id,
            len(simple_commands),
        )

        # Register for device events
        device.events.on("UPDATE", self._on_device_update)

    async def _on_device_update(
        self, entity_id: str, update_data: dict[str, Any]
    ) -> None:
        """Handle device state updates."""
        pass

    async def handle_command(
        self, entity: Remote, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")

        try:
            zone = self._zone_config.zone_number

            # CRITICAL: Check for send_cmd first
            if cmd_id != Commands.SEND_CMD:
                _LOG.warning("[%s] Unsupported command type: %s", self.id, cmd_id)
                return StatusCodes.NOT_FOUND

            if not params or "command" not in params:
                _LOG.error("[%s] Missing command parameter", self.id)
                return StatusCodes.BAD_REQUEST

            command = params["command"]
            _LOG.debug("[%s] Executing command: %s", self.id, command)

            # Listening Modes
            if command == "DOLBY_SURROUND":
                await self._device._send_command(f"Z{zone}ALM3")
                return StatusCodes.OK
            elif command == "DTS_NEURAL_X":
                await self._device._send_command(f"Z{zone}ALM4")
                return StatusCodes.OK
            elif command == "ANTHEMLOGIC_CINEMA":
                await self._device._send_command(f"Z{zone}ALM1")
                return StatusCodes.OK
            elif command == "ANTHEMLOGIC_MUSIC":
                await self._device._send_command(f"Z{zone}ALM2")
                return StatusCodes.OK
            elif command == "STEREO":
                await self._device._send_command(f"Z{zone}ALM5")
                return StatusCodes.OK
            elif command == "MULTI_CHANNEL_STEREO":
                await self._device._send_command(f"Z{zone}ALM6")
                return StatusCodes.OK
            elif command == "DIRECT":
                await self._device._send_command(f"Z{zone}ALM15")
                return StatusCodes.OK

            # Audio Mode Navigation
            elif command == "AUDIO_MODE_UP":
                await self._device._send_command(f"Z{zone}AUP")
                return StatusCodes.OK
            elif command == "AUDIO_MODE_DOWN":
                await self._device._send_command(f"Z{zone}ADN")
                return StatusCodes.OK

            # Tone Controls
            elif command == "BASS_UP":
                await self._device._send_command(f"Z{zone}TUP0")
                return StatusCodes.OK
            elif command == "BASS_DOWN":
                await self._device._send_command(f"Z{zone}TDN0")
                return StatusCodes.OK
            elif command == "TREBLE_UP":
                await self._device._send_command(f"Z{zone}TUP1")
                return StatusCodes.OK
            elif command == "TREBLE_DOWN":
                await self._device._send_command(f"Z{zone}TDN1")
                return StatusCodes.OK

            # Balance
            elif command == "BALANCE_LEFT":
                await self._device._send_command(f"Z{zone}BLT")
                return StatusCodes.OK
            elif command == "BALANCE_RIGHT":
                await self._device._send_command(f"Z{zone}BRT")
                return StatusCodes.OK

            # Dolby Settings
            elif command == "DOLBY_DRC_NORMAL":
                await self._device._send_command(f"Z{zone}DYN0")
                return StatusCodes.OK
            elif command == "DOLBY_DRC_REDUCED":
                await self._device._send_command(f"Z{zone}DYN1")
                return StatusCodes.OK
            elif command == "DOLBY_DRC_LATE_NIGHT":
                await self._device._send_command(f"Z{zone}DYN2")
                return StatusCodes.OK
            elif command == "DOLBY_CENTER_SPREAD_ON":
                await self._device._send_command(f"Z{zone}DSCS1")
                return StatusCodes.OK
            elif command == "DOLBY_CENTER_SPREAD_OFF":
                await self._device._send_command(f"Z{zone}DSCS0")
                return StatusCodes.OK

            else:
                _LOG.warning("[%s] Unknown audio command: %s", self.id, command)
                return StatusCodes.NOT_FOUND

        except Exception as err:
            _LOG.error("[%s] Error executing command %s: %s", self.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR

    @property
    def zone_number(self) -> int:
        """Get zone number."""
        return self._zone_config.zone_number

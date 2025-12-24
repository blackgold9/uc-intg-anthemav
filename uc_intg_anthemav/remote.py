"""
Anthem Remote Entity - Advanced Audio Processing Controls.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes
from ucapi.remote import Attributes, Commands, Features, Remote

from uc_intg_anthemav.config import AnthemDeviceConfig, ZoneConfig
from uc_intg_anthemav.device import AnthemDevice

_LOG = logging.getLogger(__name__)


class AnthemRemote(Remote):
    """
    Remote entity for Anthem A/V receiver advanced audio processing.
    
    Provides access to advanced features:
    - Audio Listening Modes (Dolby, DTS, AnthemLogic, etc.)
    - Tone Controls (Bass/Treble)
    - Balance Adjustments
    - Individual Speaker Levels
    - Audio Processing Settings
    """
    
    # Anthem Audio Listening Modes
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
        "Direct": 15
    }
    
    # Speaker channel mappings for level control
    SPEAKER_CHANNELS = {
        "Subwoofer": 1,
        "Front Left/Right": 5,
        "Front Wide": 6,
        "Center": 7,
        "Surround": 8,
        "Back": 9,
        "Height 1": 10,
        "Height 2": 11,
        "Height 3": 12
    }
    
    def __init__(self, device_config: AnthemDeviceConfig, device: AnthemDevice, zone_config: ZoneConfig):
        """Initialize remote entity."""
        self._device = device
        self._device_config = device_config
        self._zone_config = zone_config
        
        # Create entity ID
        if zone_config.zone_number == 1:
            entity_id = f"remote.{device_config.identifier}"
            entity_name = f"{device_config.name} Audio Controls"
        else:
            entity_id = f"remote.{device_config.identifier}.zone{zone_config.zone_number}"
            entity_name = f"{device_config.name} Zone {zone_config.zone_number} Audio Controls"
        
        # Define button mappings for Anthem audio processing
        button_mappings = [
            # Audio Listening Modes
            {"button": "DOLBY_SURROUND", "short_press": {"cmd_id": "listening_mode", "params": {"mode": "Dolby Surround"}}},
            {"button": "DTS_NEURAL_X", "short_press": {"cmd_id": "listening_mode", "params": {"mode": "DTS Neural:X"}}},
            {"button": "ANTHEMLOGIC_CINEMA", "short_press": {"cmd_id": "listening_mode", "params": {"mode": "AnthemLogic Cinema"}}},
            {"button": "ANTHEMLOGIC_MUSIC", "short_press": {"cmd_id": "listening_mode", "params": {"mode": "AnthemLogic Music"}}},
            {"button": "STEREO", "short_press": {"cmd_id": "listening_mode", "params": {"mode": "Stereo"}}},
            {"button": "MULTI_CHANNEL_STEREO", "short_press": {"cmd_id": "listening_mode", "params": {"mode": "Multi-Channel Stereo"}}},
            {"button": "DIRECT", "short_press": {"cmd_id": "listening_mode", "params": {"mode": "Direct"}}},
            
            # Audio Mode Navigation
            {"button": "AUDIO_MODE_UP", "short_press": {"cmd_id": "audio_mode_up"}},
            {"button": "AUDIO_MODE_DOWN", "short_press": {"cmd_id": "audio_mode_down"}},
            
            # Tone Controls
            {"button": "BASS_UP", "short_press": {"cmd_id": "tone_control", "params": {"control": "bass", "direction": "up"}}},
            {"button": "BASS_DOWN", "short_press": {"cmd_id": "tone_control", "params": {"control": "bass", "direction": "down"}}},
            {"button": "TREBLE_UP", "short_press": {"cmd_id": "tone_control", "params": {"control": "treble", "direction": "up"}}},
            {"button": "TREBLE_DOWN", "short_press": {"cmd_id": "tone_control", "params": {"control": "treble", "direction": "down"}}},
            
            # Balance Controls
            {"button": "BALANCE_LEFT", "short_press": {"cmd_id": "balance", "params": {"direction": "left"}}},
            {"button": "BALANCE_RIGHT", "short_press": {"cmd_id": "balance", "params": {"direction": "right"}}},
            
            # Dolby Settings
            {"button": "DOLBY_DYNAMIC_RANGE_NORMAL", "short_press": {"cmd_id": "dolby_dynamic_range", "params": {"mode": "normal"}}},
            {"button": "DOLBY_DYNAMIC_RANGE_REDUCED", "short_press": {"cmd_id": "dolby_dynamic_range", "params": {"mode": "reduced"}}},
            {"button": "DOLBY_DYNAMIC_RANGE_LATE_NIGHT", "short_press": {"cmd_id": "dolby_dynamic_range", "params": {"mode": "late_night"}}},
            
            # Dolby Surround Center Spread
            {"button": "DOLBY_CENTER_SPREAD_ON", "short_press": {"cmd_id": "dolby_center_spread", "params": {"state": "on"}}},
            {"button": "DOLBY_CENTER_SPREAD_OFF", "short_press": {"cmd_id": "dolby_center_spread", "params": {"state": "off"}}},
        ]
        
        # Define features
        features = [Features.SEND_CMD]
        
        # Initial attributes
        attributes = {
            Attributes.STATE: "ONLINE"
        }
        
        super().__init__(
            entity_id,
            entity_name,
            features,
            attributes,
            button_mapping=button_mappings,
            cmd_handler=self.handle_command
        )
        
        # Register for device events
        device.events.on("UPDATE", self._on_device_update)
    
    async def _on_device_update(self, entity_id: str, update_data: dict[str, Any]) -> None:
        """Handle device state updates."""
        # Remote entity doesn't need state updates currently
        pass
    
    async def handle_command(
        self,
        entity: Remote,
        cmd_id: str,
        params: dict[str, Any] | None
    ) -> StatusCodes:
        """Handle remote commands."""
        _LOG.info("[%s] Command: %s %s", self.id, cmd_id, params or "")
        
        try:
            zone = self._zone_config.zone_number
            
            if cmd_id == "listening_mode":
                mode = params.get("mode")
                mode_num = self.LISTENING_MODES.get(mode)
                if mode_num is not None:
                    success = await self._device._send_command(f"Z{zone}ALM{mode_num}")
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST
            
            elif cmd_id == "audio_mode_up":
                success = await self._device._send_command(f"Z{zone}AUP")
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == "audio_mode_down":
                success = await self._device._send_command(f"Z{zone}ADN")
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == "tone_control":
                control = params.get("control")  # "bass" or "treble"
                direction = params.get("direction")  # "up" or "down"
                
                control_num = 0 if control == "bass" else 1
                command = f"Z{zone}TUP{control_num}" if direction == "up" else f"Z{zone}TDN{control_num}"
                
                success = await self._device._send_command(command)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == "balance":
                direction = params.get("direction")  # "left" or "right"
                command = f"Z{zone}BLT" if direction == "left" else f"Z{zone}BRT"
                
                success = await self._device._send_command(command)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == "dolby_dynamic_range":
                mode = params.get("mode")
                mode_map = {"normal": 0, "reduced": 1, "late_night": 2}
                mode_num = mode_map.get(mode)
                
                if mode_num is not None:
                    success = await self._device._send_command(f"Z{zone}DYN{mode_num}")
                    return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
                return StatusCodes.BAD_REQUEST
            
            elif cmd_id == "dolby_center_spread":
                state = params.get("state")
                state_num = 1 if state == "on" else 0
                
                success = await self._device._send_command(f"Z{zone}DSCS{state_num}")
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            elif cmd_id == "speaker_level":
                channel = params.get("channel")
                direction = params.get("direction")
                
                channel_num = self.SPEAKER_CHANNELS.get(channel)
                if channel_num is None:
                    return StatusCodes.BAD_REQUEST
                
                command = f"Z{zone}LUP{channel_num}" if direction == "up" else f"Z{zone}LDN{channel_num}"
                
                success = await self._device._send_command(command)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
            
            else:
                _LOG.warning("[%s] Unsupported command: %s", self.id, cmd_id)
                return StatusCodes.OK
        
        except Exception as err:
            _LOG.error("[%s] Error executing command %s: %s", self.id, cmd_id, err)
            return StatusCodes.SERVER_ERROR
    
    @property
    def zone_number(self) -> int:
        """Get zone number."""
        return self._zone_config.zone_number
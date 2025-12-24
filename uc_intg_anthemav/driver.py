"""
Anthem A/V integration driver for Unfolded Circle Remote.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging

from ucapi import EntityTypes
from ucapi_framework import BaseIntegrationDriver, create_entity_id

from uc_intg_anthemav.config import AnthemConfigManager, AnthemDeviceConfig
from uc_intg_anthemav.device import AnthemDevice
from uc_intg_anthemav.media_player import AnthemMediaPlayer
from uc_intg_anthemav.remote import AnthemRemote
from uc_intg_anthemav.setup_flow import AnthemSetupFlow

_LOG = logging.getLogger(__name__)


class AnthemDriver(BaseIntegrationDriver[AnthemDevice, AnthemDeviceConfig]):
    """Anthem A/V integration driver."""
    
    def __init__(self, loop: asyncio.AbstractEventLoop):
        super().__init__(
            device_class=AnthemDevice,
            entity_classes=[],  # We'll create entities manually for multi-zone
            loop=loop,
            driver_id="anthemav"
        )
        self._entities: dict[str, AnthemMediaPlayer | AnthemRemote] = {}
    
    def create_entities(
        self,
        device_config: AnthemDeviceConfig,
        device: AnthemDevice
    ) -> list[AnthemMediaPlayer | AnthemRemote]:
        """
        Create both media player and remote entities for each zone.
        
        For each zone, creates:
        - Media player entity (power, volume, source selection)
        - Remote entity (audio modes, tone controls, balance, etc.)
        """
        entities = []
        
        for zone_config in device_config.zones:
            if not zone_config.enabled:
                continue
            
            # Create Media Player entity for basic controls
            media_player = AnthemMediaPlayer(device_config, device, zone_config)
            entities.append(media_player)
            self._entities[media_player.id] = media_player
            
            _LOG.info("Created media player: %s for %s Zone %d",
                     media_player.id, device_config.name, zone_config.zone_number)
            
            # Create Remote entity for advanced audio processing
            remote = AnthemRemote(device_config, device, zone_config)
            entities.append(remote)
            self._entities[remote.id] = remote
            
            _LOG.info("Created remote: %s for %s Zone %d audio controls",
                     remote.id, device_config.name, zone_config.zone_number)
        
        return entities
    
    def device_from_entity_id(self, entity_id: str) -> str | None:
        """
        Extract device ID from entity ID.
        
        Entity ID format:
        - Zone 1 Media Player: media_player.anthem_192_168_1_100_14999
        - Zone 1 Remote: remote.anthem_192_168_1_100_14999
        - Zone 2+ Media Player: media_player.anthem_192_168_1_100_14999.zone2
        - Zone 2+ Remote: remote.anthem_192_168_1_100_14999.zone2
        """
        if not entity_id:
            return None
        
        if "." not in entity_id:
            return None
        
        parts = entity_id.split(".")
        
        if len(parts) == 2:
            # Simple format: media_player.device_id or remote.device_id
            return parts[1]
        elif len(parts) == 3:
            # With sub-device: media_player.device_id.zone2 or remote.device_id.zone2
            return parts[1]
        
        return None
    
    def get_entity_ids_for_device(self, device_id: str) -> list[str]:
        """
        Get all entity IDs for a device.
        
        Returns entity IDs for all configured zones (both media player and remote).
        """
        device_config = self.get_device_config(device_id)
        if not device_config:
            return []
        
        entity_ids = []
        for zone in device_config.zones:
            if not zone.enabled:
                continue
            
            if zone.zone_number == 1:
                entity_ids.append(f"media_player.{device_id}")
                entity_ids.append(f"remote.{device_id}")
            else:
                entity_ids.append(f"media_player.{device_id}.zone{zone.zone_number}")
                entity_ids.append(f"remote.{device_id}.zone{zone.zone_number}")
        
        return entity_ids
    
    async def on_subscribe_entities(self, entity_ids: list[str]) -> None:
        """Handle entity subscriptions."""
        _LOG.info("=== SUBSCRIPTION HANDLER TRIGGERED ===")
        _LOG.info("Subscribed entity IDs: %s", entity_ids)
        _LOG.info("Available entities: %s", list(self._entities.keys()))
        
        for entity_id in entity_ids:
            entity = self._entities.get(entity_id)
            if entity:
                _LOG.info("[%s] Triggering initial status query", entity_id)
                await entity.push_update()
            else:
                _LOG.warning("[%s] Entity not found in storage!", entity_id)
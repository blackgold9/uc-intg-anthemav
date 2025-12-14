"""
Anthem A/V integration driver for Unfolded Circle Remote.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
from typing import Any

from ucapi import EntityTypes
from ucapi.media_player import Attributes, States
from ucapi_framework import (
    BaseConfigManager,
    BaseIntegrationDriver,
    create_entity_id,
    get_config_path,
)

from uc_intg_anthemav.config import AnthemDeviceConfig
from uc_intg_anthemav.device import AnthemDevice
from uc_intg_anthemav.media_player import AnthemMediaPlayer
from uc_intg_anthemav.setup_flow import AnthemSetupFlow

_LOG = logging.getLogger(__name__)


class AnthemDriver(BaseIntegrationDriver):
    _device_config: AnthemDeviceConfig
    _device: AnthemDevice
    """Anthem A/V integration driver."""

    # I'm thinking about ways to avoid having to override this method. You need to create an array of entities per device
    # and I do as well in some of my integrations. It would be possible to specify a piece of config that is the list of
    # sub-devices and then have the framework create one entity per sub-device automatically. But in my situation, I need
    # to create from multiple lists. (Lights, and Covers for example). So a single list wouldn't even work. And it would
    # likely be more complex to call than just overriding this method.
    def create_entities(
        self, device_config: AnthemDeviceConfig, device: AnthemDevice
    ) -> list:
        """Create media player entities for each zone."""
        entities = []

        for zone_config in device_config.zones:
            if not zone_config.enabled:
                continue

            entity_id = create_entity_id(
                EntityTypes.MEDIA_PLAYER,
                device_config.identifier,
                f"zone{zone_config.zone_number}",
            )

            entity = AnthemMediaPlayer(
                entity_id=entity_id,
                device=device,
                device_config=device_config,
                zone_config=zone_config,
            )

            entities.append(entity)
            _LOG.info(
                f"Created entity: {entity_id} for {device_config.name} Zone {zone_config.zone_number}"
            )

        return entities

    # I'm going to update the framework to not require you to call this
    def sub_device_from_entity_id(self, entity_id: str) -> str | None:
        """Extract zone identifier from entity ID."""
        parts = entity_id.split(".")
        if len(parts) == 3:
            return parts[2]
        return None

    def on_device_update(self, entity_id: str, update_data: dict[str, Any]) -> None:
        """Handle device state updates."""
        if entity_id != self._device_config.identifier:
            return

        configured_entity = self.api.configured_entities.get(entity_id)
        zone_number = self.sub_device_from_entity_id(entity_id)

        if "zone" in update_data:
            if update_data["zone"] == zone_number:
                zone_state = update_data.get("state", {})
                self._update_attributes_from_state(zone_state, configured_entity)

        if update_data.get("inputs_discovered"):
            source_list = self._device.get_input_list()
            if configured_entity.attributes.get(Attributes.SOURCE_LIST) != source_list:
                configured_entity.attributes[Attributes.SOURCE_LIST] = source_list

    def _update_attributes_from_state(
        self, zone_state: dict[str, Any], configured_entity: AnthemMediaPlayer
    ) -> None:
        """Update entity attributes from zone state."""
        updated_attrs = {}

        if "power" in zone_state:
            new_state = States.ON if zone_state["power"] else States.OFF
            if configured_entity.attributes.get(Attributes.STATE) != new_state:
                updated_attrs[Attributes.STATE] = new_state

        if "volume" in zone_state:
            volume_db = zone_state["volume"]
            volume_pct = configured_entity._db_to_percentage(volume_db)
            if (
                abs(configured_entity.attributes.get(Attributes.VOLUME, 0) - volume_pct)
                > 0.01
            ):
                updated_attrs[Attributes.VOLUME] = volume_pct

        if "muted" in zone_state:
            if (
                configured_entity.attributes.get(Attributes.MUTED)
                != zone_state["muted"]
            ):
                updated_attrs[Attributes.MUTED] = zone_state["muted"]

        if "input_name" in zone_state:
            if (
                configured_entity.attributes.get(Attributes.SOURCE)
                != zone_state["input_name"]
            ):
                updated_attrs[Attributes.SOURCE] = zone_state["input_name"]
                if zone_state["input_name"]:
                    updated_attrs[Attributes.MEDIA_TITLE] = zone_state["input_name"]

        if "audio_format" in zone_state:
            if zone_state["audio_format"]:
                updated_attrs[Attributes.MEDIA_TYPE] = zone_state["audio_format"]

        if updated_attrs:
            configured_entity.attributes.update(updated_attrs)


# I deleted __init__ and main and moved the logic here and updated build.yml to point to this file as the driver entry point.
# This conforms to the way the official integrations are structured.
async def main():
    """Main entry point for Anthem integration."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    driver = AnthemDriver(device_class=AnthemDevice, entity_classes=[AnthemMediaPlayer])

    config_manager = BaseConfigManager[AnthemDeviceConfig](
        get_config_path(driver.api.config_dir_path),
        driver.on_device_added,
        driver.on_device_removed,
        config_class=AnthemDeviceConfig,
    )

    setup_flow = AnthemSetupFlow(config_manager)

    await driver.api.init("driver.json", setup_flow)

    # Keep the driver running
    await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())

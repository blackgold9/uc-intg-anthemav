"""
Configuration management for Anthem A/V integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_LOG = logging.getLogger(__name__)


@dataclass
class ZoneConfig:
    zone_number: int
    enabled: bool = True
    name: str = None
    
    def __post_init__(self):
        if self.name is None:
            self.name = f"Zone {self.zone_number}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "zone_number": self.zone_number,
            "enabled": self.enabled,
            "name": self.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ZoneConfig":
        return cls(
            zone_number=data["zone_number"],
            enabled=data.get("enabled", True),
            name=data.get("name")
        )


@dataclass
class DeviceConfig:
    device_id: str
    name: str
    ip_address: str
    model: str
    port: int = 14999
    timeout: int = 10
    enabled: bool = True
    zones: List[ZoneConfig] = None
    
    def __post_init__(self):
        if self.zones is None:
            self.zones = [ZoneConfig(1)]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "ip_address": self.ip_address,
            "model": self.model,
            "port": self.port,
            "timeout": self.timeout,
            "enabled": self.enabled,
            "zones": [zone.to_dict() for zone in self.zones]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DeviceConfig":
        zones_data = data.get("zones", [{"zone_number": 1}])
        zones = [ZoneConfig.from_dict(z) for z in zones_data]
        
        return cls(
            device_id=data["device_id"],
            name=data["name"],
            ip_address=data["ip_address"],
            model=data["model"],
            port=data.get("port", 14999),
            timeout=data.get("timeout", 10),
            enabled=data.get("enabled", True),
            zones=zones
        )


class AnthemConfig:
    
    def __init__(self, config_file_path: str = "config.json"):
        self._config_file_path = config_file_path
        self._devices: List[DeviceConfig] = []
        self._loaded = False
        
        config_dir = os.path.dirname(self._config_file_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
        
        self._load_config()
    
    def _load_config(self) -> None:
        try:
            if os.path.exists(self._config_file_path):
                with open(self._config_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    
                devices_data = data.get("devices", [])
                self._devices = [DeviceConfig.from_dict(device_data) for device_data in devices_data]
                
                _LOG.info(f"Loaded configuration with {len(self._devices)} devices")
                self._loaded = True
            else:
                _LOG.info("No existing configuration file found")
                self._devices = []
                self._loaded = True
        except Exception as e:
            _LOG.error(f"Failed to load configuration: {e}")
            self._devices = []
            self._loaded = True
    
    def _save_config(self) -> None:
        try:
            config_data = {
                "devices": [device.to_dict() for device in self._devices],
                "version": "1.0.0"
            }
            
            with open(self._config_file_path, 'w', encoding='utf-8') as file:
                json.dump(config_data, file, indent=2, ensure_ascii=False)
            
            _LOG.info(f"Saved configuration with {len(self._devices)} devices")
        except Exception as e:
            _LOG.error(f"Failed to save configuration: {e}")
            raise
    
    def reload_from_disk(self) -> None:
        _LOG.debug("Reloading configuration from disk")
        self._load_config()
    
    def is_configured(self) -> bool:
        return self._loaded and len(self._devices) > 0
    
    def add_device(self, device: DeviceConfig) -> None:
        existing_ids = [d.device_id for d in self._devices]
        if device.device_id in existing_ids:
            raise ValueError(f"Device ID {device.device_id} already exists")
        
        self._devices.append(device)
        self._save_config()
        _LOG.info(f"Added device: {device.name} ({device.model}) at {device.ip_address}")
    
    def remove_device(self, device_id: str) -> bool:
        original_count = len(self._devices)
        self._devices = [d for d in self._devices if d.device_id != device_id]
        
        if len(self._devices) < original_count:
            self._save_config()
            _LOG.info(f"Removed device: {device_id}")
            return True
        return False
    
    def get_device(self, device_id: str) -> Optional[DeviceConfig]:
        for device in self._devices:
            if device.device_id == device_id:
                return device
        return None
    
    def get_all_devices(self) -> List[DeviceConfig]:
        return self._devices.copy()
    
    def get_enabled_devices(self) -> List[DeviceConfig]:
        return [device for device in self._devices if device.enabled]
    
    def update_device(self, device_id: str, **kwargs) -> bool:
        device = self.get_device(device_id)
        if not device:
            return False
        
        allowed_fields = ['name', 'ip_address', 'model', 'port', 'timeout', 'enabled']
        updated = False
        
        for field, value in kwargs.items():
            if field in allowed_fields and hasattr(device, field):
                setattr(device, field, value)
                updated = True
        
        if updated:
            self._save_config()
            _LOG.info(f"Updated device: {device_id}")
        
        return updated
    
    def clear_all_devices(self) -> None:
        self._devices = []
        self._save_config()
        _LOG.info("Cleared all device configurations")
    
    def validate_device_config(self, device: DeviceConfig) -> List[str]:
        errors = []
        
        if not device.device_id or not device.device_id.strip():
            errors.append("Device ID cannot be empty")
        
        if not device.name or not device.name.strip():
            errors.append("Device name cannot be empty")
        
        if not device.ip_address or not device.ip_address.strip():
            errors.append("IP address cannot be empty")
        
        ip_parts = device.ip_address.split('.')
        if len(ip_parts) != 4:
            errors.append("Invalid IP address format")
        else:
            for part in ip_parts:
                try:
                    num = int(part)
                    if num < 0 or num > 255:
                        errors.append("Invalid IP address range")
                        break
                except ValueError:
                    errors.append("Invalid IP address format")
                    break
        
        if device.port < 1 or device.port > 65535:
            errors.append("Port must be between 1 and 65535")
        
        if device.timeout < 1 or device.timeout > 60:
            errors.append("Timeout must be between 1 and 60 seconds")
        
        return errors
    
    def get_device_count(self) -> int:
        return len(self._devices)
    
    def get_enabled_device_count(self) -> int:
        return len(self.get_enabled_devices())
    
    def get_summary(self) -> Dict[str, Any]:
        total_zones = sum(len(d.zones) for d in self._devices)
        
        return {
            "total_devices": len(self._devices),
            "enabled_devices": len(self.get_enabled_devices()),
            "total_zones": total_zones,
            "configured": self.is_configured(),
            "config_file": self._config_file_path
        }
    
    @property
    def config_file_path(self) -> str:
        return self._config_file_path
import pytest
from unittest.mock import MagicMock, patch, ANY
from uc_intg_anthemav.device import AnthemDevice
from uc_intg_anthemav.config import AnthemDeviceConfig
from uc_intg_anthemav.models import ZoneAudioFormat
from ucapi_framework import DeviceEvents

@pytest.fixture
def mock_config():
    config = MagicMock(spec=AnthemDeviceConfig)
    config.identifier = "test_receiver"
    config.name = "Test Receiver"
    config.host = "192.168.1.100"
    config.port = 14999
    config.zones = []
    return config

def test_is_sensor_zone(mock_config):
    device = AnthemDevice(mock_config)
    assert device._is_sensor_zone(1) is True
    assert device._is_sensor_zone(2) is False
    assert device._is_sensor_zone(3) is False

def test_sensor_update_emitted_only_for_zone1(mock_config):
    device = AnthemDevice(mock_config)
    device.events = MagicMock()
    
    # Test Zone 1
    message_z1 = ZoneAudioFormat(zone=1, format="Dolby Atmos")
    device._handle_message(message_z1)
    
    # Check if emit was called for zone 1
    # Note: sensor_id is f"sensor.{device.identifier}_audio_format"
    expected_sensor_id = f"sensor.{device.identifier}_audio_format"
    device.events.emit.assert_any_call(DeviceEvents.UPDATE, expected_sensor_id, ANY)
    
    # Reset mock
    device.events.emit.reset_mock()
    
    # Test Zone 2
    message_z2 = ZoneAudioFormat(zone=2, format="Stereo")
    device._handle_message(message_z2)
    
    # Check if emit was NOT called for zone 2
    device.events.emit.assert_not_called()

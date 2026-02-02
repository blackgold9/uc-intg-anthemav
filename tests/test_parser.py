import pytest
from uc_intg_anthemav.models import (
    SystemModel, InputCount, InputName,
    ZonePower, ZoneVolume, ZoneMute, ZoneInput,
    ZoneAudioFormat, ZoneAudioChannels, ZoneVideoResolution,
    ZoneListeningMode, ZoneSampleRateInfo, ZoneSampleRate, ZoneBitDepth
)
from uc_intg_anthemav.parser import parse_message

def test_system_messages():
    assert parse_message("IDM MRX 1120") == SystemModel(model="MRX 1120")
    assert parse_message("ICN15") == InputCount(count=15)
    assert parse_message("IS1INHDMI 1") == InputName(input_number=1, name="HDMI 1")

def test_zone_power():
    assert parse_message("Z1POW1") == ZonePower(zone=1, is_on=True)
    assert parse_message("Z1POW0") == ZonePower(zone=1, is_on=False)
    assert parse_message("Z2POW1") == ZonePower(zone=2, is_on=True)

def test_zone_volume():
    assert parse_message("Z1VOL-35") == ZoneVolume(zone=1, volume_db=-35)
    assert parse_message("Z1VOL0") == ZoneVolume(zone=1, volume_db=0)
    assert parse_message("Z1VOL-90") == ZoneVolume(zone=1, volume_db=-90)

def test_zone_mute():
    assert parse_message("Z1MUT1") == ZoneMute(zone=1, is_muted=True)
    assert parse_message("Z1MUT0") == ZoneMute(zone=1, is_muted=False)

def test_zone_input():
    assert parse_message("Z1INP1") == ZoneInput(zone=1, input_number=1)
    assert parse_message("Z1INP15") == ZoneInput(zone=1, input_number=15)

def test_sensor_data():
    assert parse_message("Z1AIFDolby Atmos") == ZoneAudioFormat(zone=1, format="Dolby Atmos")
    assert parse_message("Z1AIC7.1.4") == ZoneAudioChannels(zone=1, channels="7.1.4")
    assert parse_message("Z1VIR4K") == ZoneVideoResolution(zone=1, resolution="4K")

    # Listening Mode 3 is Dolby Surround
    expected_mode = ZoneListeningMode(zone=1, mode_number=3, mode_name="Dolby Surround")
    assert parse_message("Z1ALM3") == expected_mode

    assert parse_message("Z1AIR48kHz") == ZoneSampleRateInfo(zone=1, info="48kHz")
    assert parse_message("Z1SRT48") == ZoneSampleRate(zone=1, rate_khz=48)
    assert parse_message("Z1BDP24") == ZoneBitDepth(zone=1, depth=24)

def test_ignored_messages():
    assert parse_message("!I0") is None
    assert parse_message("!E1") is None
    assert parse_message("") is None
    assert parse_message("GARBAGE") is None

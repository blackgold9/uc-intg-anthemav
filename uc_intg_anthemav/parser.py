import re
from typing import Optional
from .models import (
    ParsedMessage, SystemModel, InputCount, InputName,
    ZonePower, ZoneVolume, ZoneMute, ZoneInput,
    ZoneAudioFormat, ZoneAudioChannels, ZoneVideoResolution,
    ZoneListeningMode, ZoneSampleRateInfo, ZoneSampleRate, ZoneBitDepth
)
from .constants import MessagePrefixes

def _get_listening_mode_name(mode_num: int) -> str:
    """Convert listening mode number to friendly name."""
    mode_names = {
        0: "None",
        1: "AnthemLogic Cinema",
        2: "AnthemLogic Music",
        3: "Dolby Surround",
        4: "DTS Neural:X",
        5: "Stereo",
        6: "Multi-Channel Stereo",
        7: "All-Channel Stereo",
        8: "PLIIx Movie",
        9: "PLIIx Music",
        10: "Neo:6 Cinema",
        11: "Neo:6 Music",
        12: "Dolby Digital",
        13: "DTS",
        14: "PCM Stereo",
        15: "Direct",
    }
    return mode_names.get(mode_num, f"Mode {mode_num}")

def parse_message(response: str) -> Optional[ParsedMessage]:
    """Parse a raw response string from the Anthem receiver."""
    if not response:
        return None

    # Error responses (ignored for state updates)
    if response.startswith(MessagePrefixes.ERROR_INVALID_COMMAND) or response.startswith(MessagePrefixes.ERROR_EXECUTION_FAILED):
        return None

    # System Messages
    if response.startswith(MessagePrefixes.SYSTEM_MODEL):
        return SystemModel(model=response[3:].strip())

    icn_match = re.match(r"ICN(\d+)", response)
    if icn_match:
        return InputCount(count=int(icn_match.group(1)))

    is_match = re.match(r"IS(\d{1,2})IN(.+)", response)
    if is_match:
        return InputName(input_number=int(is_match.group(1)), name=is_match.group(2).strip())

    # Zone Messages
    # Matches Z<zone><command>
    zone_match = re.match(r"Z(\d+)(.+)", response)
    if zone_match:
        zone_num = int(zone_match.group(1))
        payload = zone_match.group(2)

        if "POW" in payload:
            return ZonePower(zone=zone_num, is_on="1" in payload)

        if "VOL" in payload:
            vol_match = re.search(r"VOL(-?\d+)", payload)
            if vol_match:
                return ZoneVolume(zone=zone_num, volume_db=int(vol_match.group(1)))

        if "MUT" in payload:
            return ZoneMute(zone=zone_num, is_muted="1" in payload)

        if "INP" in payload:
            inp_match = re.search(r"INP(\d+)", payload)
            if inp_match:
                return ZoneInput(zone=zone_num, input_number=int(inp_match.group(1)))

        # Sensor data
        if "AIF" in payload:
            format_match = re.search(r"AIF(.+)", payload)
            if format_match:
                return ZoneAudioFormat(zone=zone_num, format=format_match.group(1).strip())

        if "AIC" in payload:
            channels_match = re.search(r"AIC(.+)", payload)
            if channels_match:
                return ZoneAudioChannels(zone=zone_num, channels=channels_match.group(1).strip())

        if "VIR" in payload:
            res_match = re.search(r"VIR(.+)", payload)
            if res_match:
                return ZoneVideoResolution(zone=zone_num, resolution=res_match.group(1).strip())

        if "ALM" in payload and "?" not in payload:
            mode_match = re.search(r"ALM(\d+)", payload)
            if mode_match:
                mode_num = int(mode_match.group(1))
                return ZoneListeningMode(
                    zone=zone_num,
                    mode_number=mode_num,
                    mode_name=_get_listening_mode_name(mode_num)
                )

        if "AIR" in payload:
            rate_match = re.search(r"AIR(.+)", payload)
            if rate_match:
                return ZoneSampleRateInfo(zone=zone_num, info=rate_match.group(1).strip())

        if "SRT" in payload:
            rate_match = re.search(r"SRT(\d+)", payload)
            if rate_match:
                return ZoneSampleRate(zone=zone_num, rate_khz=int(rate_match.group(1)))

        if "BDP" in payload:
            depth_match = re.search(r"BDP(\d+)", payload)
            if depth_match:
                return ZoneBitDepth(zone=zone_num, depth=int(depth_match.group(1)))

    return None

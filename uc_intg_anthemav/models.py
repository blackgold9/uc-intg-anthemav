from dataclasses import dataclass, field
from typing import Optional, Any

@dataclass
class ZoneState:
    """Represents the state of a single zone."""
    power: bool = False
    volume_db: int = -90
    muted: bool = False
    input_number: int = 1
    input_name: str = "Unknown"
    audio_format: str = "Unknown"
    audio_channels: str = "Unknown"
    video_resolution: str = "Unknown"
    listening_mode: str = "Unknown"
    sample_rate: str = "Unknown"

    def get(self, key: str, default: Any = None) -> Any:
        """Helper to access attributes like a dictionary."""
        return getattr(self, key, default)

@dataclass
class ParsedMessage:
    """Base class for all parsed messages."""
    pass

@dataclass
class SystemModel(ParsedMessage):
    """Device model name (IDM)."""
    model: str

@dataclass
class InputCount(ParsedMessage):
    """Number of inputs (ICN)."""
    count: int

@dataclass
class InputName(ParsedMessage):
    """Custom input name (IS...IN)."""
    input_number: int
    name: str

@dataclass
class ZoneMessage(ParsedMessage):
    """Base class for zone-specific messages."""
    zone: int

@dataclass
class ZonePower(ZoneMessage):
    """Zone power state (Z...POW)."""
    is_on: bool

@dataclass
class ZoneVolume(ZoneMessage):
    """Zone volume in dB (Z...VOL)."""
    volume_db: int

@dataclass
class ZoneMute(ZoneMessage):
    """Zone mute state (Z...MUT)."""
    is_muted: bool

@dataclass
class ZoneInput(ZoneMessage):
    """Zone input selection (Z...INP)."""
    input_number: int

@dataclass
class ZoneAudioFormat(ZoneMessage):
    """Audio input format (Z...AIF)."""
    format: str

@dataclass
class ZoneAudioChannels(ZoneMessage):
    """Audio input channels (Z...AIC)."""
    channels: str

@dataclass
class ZoneVideoResolution(ZoneMessage):
    """Video input resolution (Z...VIR)."""
    resolution: str

@dataclass
class ZoneListeningMode(ZoneMessage):
    """Listening mode (Z...ALM)."""
    mode_name: str
    mode_number: int

@dataclass
class ZoneSampleRateInfo(ZoneMessage):
    """Full sample rate info string (Z...AIR)."""
    info: str

@dataclass
class ZoneSampleRate(ZoneMessage):
    """Sample rate in kHz (Z...SRT)."""
    rate_khz: int

@dataclass
class ZoneBitDepth(ZoneMessage):
    """Bit depth (Z...BDP)."""
    depth: int

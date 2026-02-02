from enum import StrEnum

class MessagePrefixes(StrEnum):
    ERROR_INVALID_COMMAND = "!I"
    ERROR_EXECUTION_FAILED = "!E"
    SYSTEM_MODEL = "IDM"
    INPUT_COUNT = "ICN"
    INPUT_SETUP = "IS"
    ZONE_PREFIX = "Z"

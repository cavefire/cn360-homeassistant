"""Constants for the 360 Robot integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "cn360"

# Configuration constants
CONF_IP = "ip"
CONF_PORT = "port"

# Default values
DEFAULT_NAME = "360 Robot"

# Services
SERVICE_START_CLEANING = "start_cleaning"
SERVICE_PAUSE = "pause"
SERVICE_RESUME = "resume"
SERVICE_RETURN_TO_BASE = "return_to_base"
SERVICE_SET_CLEANING_MODE = "set_cleaning_mode"

# Update intervals
UPDATE_INTERVAL_LOCAL = timedelta(seconds=5)  # 5 seconds for local polling


# Errors
ERROR_NO_WATERTANK = -2602
ERROR_NO_DUSTBIN = -2406
ERROR_FLOOR_UNEVEN = -2304
ERROR_NOT_ON_FLOOR = -2601
ERROR_STUCK = -2502

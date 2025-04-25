"""Support for 360 Robot vacuums."""

from __future__ import annotations

from collections.abc import Mapping
import json
import logging
from typing import Any

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import CN360BaseEntity

_LOGGER = logging.getLogger(__name__)

# Map API modes to Home Assistant VacuumActivity
ACTIVITY_MAPPING = {
    "dormant": VacuumActivity.IDLE,
    "pause": VacuumActivity.PAUSED,
    "charge": VacuumActivity.DOCKED,
    "fullcharge": VacuumActivity.DOCKED,
    "backcharge": VacuumActivity.RETURNING,
    "rfctrl": VacuumActivity.CLEANING,
    "sweep": VacuumActivity.CLEANING,
}

FAN_SPEEDS = [
    "quiet",
    "auto",
    "strong",
    "max",
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up 360 Robot vacuum based on a config entry."""

    vacuum = CN360Vacuum(hass, entry)
    async_add_entities([vacuum])


class CN360Vacuum(CN360BaseEntity, StateVacuumEntity):
    """Representation of a 360 Robot vacuum cleaner."""

    _attr_fan_speed_list = FAN_SPEEDS
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the 360 Robot vacuum."""
        super().__init__(hass, entry)
        self.hass = hass
        self._entry_id = entry.entry_id
        self._attr_unique_id = entry.entry_id
        self._attr_name = "360 Robot"

        def _update_callback() -> None:
            """Handle updates from the coordinator."""
            self.schedule_update_ha_state()

        # when coordinator updates it data
        self._coordinator.async_add_listener(_update_callback)

    @property
    def activity(self) -> VacuumActivity:
        """Return the state of the vacuum cleaner as a VacuumActivity enum value."""
        mode = self._coordinator.getRobotData().get("mode", "dormant")
        return ACTIVITY_MAPPING.get(mode, VacuumActivity.IDLE)

    @property
    def battery_level(self) -> int | None:
        """Return the battery level of the vacuum cleaner."""
        return self._coordinator.getRobotData().get("elec", 0)

    @property
    def fan_speed(self) -> str | None:
        """Return the fan speed of the vacuum cleaner."""
        return self._coordinator.getRobotData().get("workNoisy", "auto")

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return device specific state attributes."""
        return {
            "Total area cleaned (m2)": self._coordinator.getRobotData().get(
                "allArea", 0
            ),
            "Total time cleaned (min)": self._coordinator.getRobotData().get(
                "allTime", 0
            ),
            "Area": json.dumps(
                self._coordinator.getRobotData().get("area", {}), indent=2
            ),
            "Auto Boost": "On"
            if self._coordinator.getRobotData().get("autoBoost", 0) == 1
            else "Off",
            "Charge Handle Phi": self._coordinator.getRobotData().get(
                "chargeHandlePhi", 0
            ),
            "Charge Handle Position X": self._coordinator.getRobotData().get(
                "chargeHandlePos", [0, 0]
            )[0],
            "Charge Handle Position Y": self._coordinator.getRobotData().get(
                "chargeHandlePos", [0, 0]
            )[1],
            "Charge Handle State": self._coordinator.getRobotData().get(
                "chargeHandleState", 0
            ),
            "Clean Area": self._coordinator.getRobotData().get("cleanArea", 0),
            "Clean ID": self._coordinator.getRobotData().get("cleanId", "None"),
            "Clean ID 2": self._coordinator.getRobotData().get("cleanId2", "None"),
            "Clean Time": self._coordinator.getRobotData().get("cleanTime", 0),
            "Battery Percentage": self._coordinator.getRobotData().get("elec", 0),
            "Real Battery Percentage": self._coordinator.getRobotData().get(
                "elecReal", 0
            ),
            "Error State": json.dumps(
                self._coordinator.getRobotData().get("errorState", [0])
            ),
            "Error Time": self._coordinator.getRobotData().get("errorTime", 0),
            "Height": self._coordinator.getRobotData().get("height", 0),
            "Last Sub Mode": self._coordinator.getRobotData().get(
                "lastSubMode", 0
            ),  # null, total, smart
            "LED": "On"
            if self._coordinator.getRobotData().get("led", 0) == 1
            else "Off",
            "Map ID": self._coordinator.getRobotData().get("mapId", 0),
            "Mode": self._coordinator.getRobotData().get(
                "mode", 0
            ),  # backcharge, charge, fullcharge, idle, rfctrl, sweep
            "Mop status": "On"
            if self._coordinator.getRobotData().get("mopStatus", 0) == 1
            else "Off",
            "Path ID": self._coordinator.getRobotData().get("pathId", 0),
            "Phi": self._coordinator.getRobotData().get("phi", 0),
            "Position X": self._coordinator.getRobotData().get("pos", [0, 0])[0],
            "Position Y": self._coordinator.getRobotData().get("pos", [0, 0])[1],
            "Reliable": self._coordinator.getRobotData().get("reliable", 0),
            "Resolution": self._coordinator.getRobotData().get("resolution", 0),
            "Show smart area": "On"
            if self._coordinator.getRobotData().get("showSmartArea", 0) == 1
            else "Off",
            "Show sweep area": "On"
            if self._coordinator.getRobotData().get("showSweepArea", 0) == 1
            else "Off",
            "Soft": "On"
            if self._coordinator.getRobotData().get("soft", 0) == 1
            else "Off",
            "Sub Mode": self._coordinator.getRobotData().get("subMode", 0),
            "Timer Status": self._coordinator.getRobotData().get("timerStatus", 0),
            "Volume": self._coordinator.getRobotData().get("volume", 0),
            "Water": self._coordinator.getRobotData().get("water", 0),
            "Width": self._coordinator.getRobotData().get("width", 0),
            "Wind Power": self._coordinator.getRobotData().get("windPower", 0),
            "Fan (Work Noisy)": self._coordinator.getRobotData().get("workNoisy", 0),
            "x min": self._coordinator.getRobotData().get("x_min", 0),
            "y min": self._coordinator.getRobotData().get("y_min", 0),
        }

    async def async_pause(self, **kwargs: Any) -> None:
        """Pause the cleaning cycle."""
        await self._coordinator.sendCommand(21017, {"cmd": "pause"})

    async def async_stop(self, **kwargs):
        """Stop returning to dock."""
        await self._coordinator.sendCommand(21012, {"cmd": "stop"})

    async def async_start(self, **kwargs: Any) -> None:
        """Resume the cleaning cycle."""
        await self._coordinator.sendCommand(
            21005, {"mode": "smartClean", "globalCleanTimes": 1}
        )

    async def async_return_to_base(self, **kwargs: Any) -> None:
        """Set the vacuum cleaner to return to the dock."""
        await self._coordinator.sendCommand(21012, {"cmd": "start"})

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        """Set fan speed."""
        if fan_speed not in FAN_SPEEDS:
            raise FanModeNotSupportedException(f"Fan speed {fan_speed} not available")
        await self._coordinator.sendCommand(
            21022, {"cmd": fan_speed, "cleanType": "total"}
        )

    @property
    def supported_features(self) -> VacuumEntityFeature:
        """Supported features."""
        return (
            (
                VacuumEntityFeature.PAUSE
                if self.activity == VacuumActivity.CLEANING
                else 0
            )
            | (
                VacuumEntityFeature.START
                if self.activity
                in [VacuumActivity.PAUSED, VacuumActivity.DOCKED, VacuumActivity.IDLE]
                else 0
            )
            | (
                VacuumEntityFeature.RETURN_HOME
                if self.activity
                not in [VacuumActivity.DOCKED, VacuumActivity.RETURNING]
                else 0
            )
            | (
                VacuumEntityFeature.STOP
                if self.activity == VacuumActivity.RETURNING
                else 0
            )
            | VacuumEntityFeature.STATUS
            | VacuumEntityFeature.BATTERY
            | VacuumEntityFeature.FAN_SPEED
        )


class FanModeNotSupportedException(HomeAssistantError):
    """Error to indicate fanmode is not supported."""

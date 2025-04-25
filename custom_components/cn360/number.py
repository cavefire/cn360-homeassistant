"""Switch."""

from collections.abc import Callable
from typing import Any

from homeassistant.components.number import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_STEP,
    ATTR_VALUE,
    NumberDeviceClass,
    NumberEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .entity import CN360BaseEntity, CN360Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up 360 Robot vacuum based on a config entry."""

    entites = [
        CN360BaseNumber(
            hass,
            entry,
            lambda coordinator: (coordinator.getRobotData().get("vol", 0) * 10),
            lambda coordinator, val: (
                coordinator.sendCommand(21024, {"cmd": "setVolume", "value": val / 10})
            ),
            "Volume",
            "volume",
            None,
            EntityCategory.CONFIG,
            max_value=100,
            min_value=0,
            step=10,
        )
    ]

    async_add_entities(entites)


class CN360BaseNumber(CN360BaseEntity, NumberEntity):
    """Generic binary sensor for CN360."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        getter: Callable[[CN360Coordinator], float],
        action: Callable[[CN360Coordinator, float], None],
        name: str,
        uid: str,
        dev_class: NumberDeviceClass | None = None,
        category: EntityCategory | None = None,
        min_value: int = 0,
        max_value: int = 100,
        step: int = 1,
    ) -> None:
        """Init function."""
        super().__init__(hass, entry)
        self._attr_name = name
        self._attr_unique_id = f"{self._coordinator.getSerialNumber()}_{uid}"
        self._attr_device_class = dev_class
        self._getter = getter
        self._action = action
        self._attr_entity_category = category

        self._attr_min_value = min_value
        self._attr_max_value = max_value
        self._attr_step = step

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        await self._action(self._coordinator, value)

    @property
    def capability_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            ATTR_MIN: self._attr_min_value,
            ATTR_MAX: self._attr_max_value,
            ATTR_STEP: self._attr_step,
        }

    @property
    def value(self) -> int | None:
        """Return the current value."""
        return self._getter(self._coordinator)

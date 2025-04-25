"""Switch."""

from collections.abc import Callable
from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
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
        CN360BaseSwitch(
            hass,
            entry,
            lambda coordinator: (coordinator.getRobotData().get("led", 0) == 1),
            lambda coordinator, val: (
                coordinator.sendCommand(
                    21024, {"cmd": "setledswitch", "value": 1 if val else 0}
                )
            ),
            "LED",
            "led",
            None,
            EntityCategory.CONFIG,
        ),
        CN360BaseSwitch(
            hass,
            entry,
            lambda coordinator: (coordinator.getRobotData().get("soft", 0) == 1),
            lambda coordinator, val: (
                coordinator.sendCommand(
                    21024, {"cmd": "setSoftAlongWall", "value": 1 if val else 0}
                )
            ),
            "Collision prevention",
            "collision_prevention",
            None,
            EntityCategory.CONFIG,
        ),
        CN360BaseSwitch(
            hass,
            entry,
            lambda coordinator: (coordinator.getRobotData().get("autoBoost", 0) == 1),
            lambda coordinator, val: (
                coordinator.sendCommand(
                    21024, {"cmd": "setAutoBoost", "value": 1 if val else 0}
                )
            ),
            "Carpet auto boost",
            "auto_boost",
            None,
            EntityCategory.CONFIG,
        ),
    ]

    async_add_entities(entites)


class CN360BaseSwitch(CN360BaseEntity, SwitchEntity):
    """Generic binary sensor for CN360."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        getter: Callable[[CN360Coordinator], bool],
        action: Callable[[CN360Coordinator, bool], None],
        name: str,
        uid: str,
        dev_class: SwitchDeviceClass | None = None,
        category: EntityCategory | None = None,
    ) -> None:
        """Init function."""
        super().__init__(hass, entry)
        self._attr_name = name
        self._attr_unique_id = f"{self._coordinator.getSerialNumber()}_{uid}"
        self._attr_device_class = dev_class
        self._getter = getter
        self._action = action
        self._attr_entity_category = category

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self._getter(self._coordinator)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self._action(self._coordinator, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self._action(self._coordinator, False)

"""Binary sensors."""

from collections.abc import Callable

from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
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
        CN360BaseButton(
            hass,
            entry,
            lambda coordinator: (
                coordinator.sendCommand(21024, {"cmd": "reboot", "value": 20})
            ),
            "Reboot",
            "reboot",
            ButtonDeviceClass.RESTART,
            EntityCategory.CONFIG,
        ),
        CN360BaseButton(
            hass,
            entry,
            lambda coordinator: (coordinator.sendCommand(21020, {"ctrlCode": 3010})),
            "Locate",
            "locate",
            ButtonDeviceClass.IDENTIFY,
            EntityCategory.DIAGNOSTIC,
        ),
    ]

    async_add_entities(entites)


class CN360BaseButton(CN360BaseEntity, ButtonEntity):
    """Generic binary sensor for CN360."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        action: Callable[[CN360Coordinator], None],
        name: str,
        uid: str,
        dev_class: ButtonDeviceClass = None,
        category: EntityCategory = None,
    ) -> None:
        """Init function."""
        super().__init__(hass, entry)
        self._attr_name = name
        self._attr_unique_id = f"{self._coordinator.getSerialNumber()}_{uid}"
        self._attr_device_class = dev_class
        self._action = action
        self._attr_entity_category = category

    async def async_press(self) -> None:
        """Call action."""
        await self._action(self._coordinator)

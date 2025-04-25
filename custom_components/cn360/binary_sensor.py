"""Binary sensors."""

from collections.abc import Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ERROR_NO_DUSTBIN, ERROR_NO_WATERTANK
from .entity import CN360BaseEntity, CN360Coordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up 360 Robot vacuum based on a config entry."""

    entites = [
        CN360BaseBinarySensor(
            hass,
            entry,
            lambda coordinator: (bool(coordinator.getRobotData().get("mopStatus", 0))),
            "Mop installed",
            "mop",
        ),
        CN360BaseBinarySensor(
            hass,
            entry,
            lambda coordinator: (
                ERROR_NO_DUSTBIN not in coordinator.getRobotData().get("errorState", [])
            ),
            "Dust bin installed",
            "dust_bin_installed",
        ),
        CN360BaseBinarySensor(
            hass,
            entry,
            lambda coordinator: (
                ERROR_NO_WATERTANK
                not in coordinator.getRobotData().get("errorState", [])
            ),
            "Water tank installed",
            "water_tank_installed",
        ),
        CN360BaseBinarySensor(
            hass,
            entry,
            lambda coordinator: (coordinator.isRobotConnected()),
            "Robot connected",
            "robot_connected",
            dev_class=BinarySensorDeviceClass.CONNECTIVITY,
            category=EntityCategory.DIAGNOSTIC,
        ),
        CN360BaseBinarySensor(
            hass,
            entry,
            lambda coordinator: (coordinator.isCloudConnected()),
            "Cloud connected",
            "cloud_connected",
            dev_class=BinarySensorDeviceClass.CONNECTIVITY,
            category=EntityCategory.DIAGNOSTIC,
        ),
    ]

    async_add_entities(entites)


class CN360BaseBinarySensor(CN360BaseEntity, BinarySensorEntity):
    """Generic binary sensor for CN360."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        getter: Callable[[CN360Coordinator], bool],
        name: str,
        uid: str,
        dev_class: BinarySensorDeviceClass = None,
        category: EntityCategory = None,
    ) -> None:
        """Init function."""
        super().__init__(hass, entry)
        self._attr_name = name
        self._attr_unique_id = f"{self._coordinator.getSerialNumber()}_{uid}"
        self._attr_device_class = dev_class
        self._getter = getter
        self._attr_entity_category = category

    @property
    def is_on(self) -> bool | None:
        """Returns value from getter."""
        return self._getter(self._coordinator)

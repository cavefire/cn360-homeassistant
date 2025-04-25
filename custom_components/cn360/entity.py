"""Entity base class."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity

from .const import DOMAIN
from .coordinator import CN360Coordinator


class CN360BaseEntity(Entity):
    """Entity base class."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Init."""
        self._coordinator: CN360Coordinator = hass.data[DOMAIN][entry.entry_id][
            "coordinator"
        ]
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._coordinator.getSerialNumber())},
            "manufacturer": "360",
            "serial_number": self._coordinator.getSerialNumber(),
            "name": self._coordinator.getSerialNumber(),
        }

        def _update_callback() -> None:
            """Handle updates from the coordinator."""
            self.schedule_update_ha_state()

        self._coordinator.async_add_listener(_update_callback)

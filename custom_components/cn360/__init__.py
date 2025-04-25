"""Integration for 360 Robot vacuum cleaners."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import CN360Coordinator, async_setup_coordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.IMAGE,
    Platform.NUMBER,
    Platform.SWITCH,
    Platform.VACUUM,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up 360 Robot from a config entry."""
    coordinator: CN360Coordinator = await async_setup_coordinator(hass, entry)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
    }

    entry.async_create_task(hass, setup_enties(hass, entry, coordinator))

    return True


async def setup_enties(
    hass: HomeAssistant, entry: ConfigEntry, coordinator: CN360Coordinator
):
    """Wait for serial number before adding platforms."""
    while not coordinator.getSerialNumber():
        await asyncio.sleep(1)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await coordinator.async_update_listeners()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Disconnect from robot socket
    if unload_ok and entry.entry_id in hass.data.get(DOMAIN, {}):
        coordinator: CN360Coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
        hass.async_add_executor_job(coordinator.disconnect)

        hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)

    return unload_ok

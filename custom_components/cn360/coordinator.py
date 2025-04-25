"""Coordinator."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import CONF_IP, CONF_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


class CN360Coordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching CN360 robot vacuum data and sending commands."""

    def __init__(
        self,
        hass: HomeAssistant,
        local_server_ip: str,
        local_server_port: int,
    ) -> None:
        """Initialize data update coordinator and connection."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{local_server_ip}_{local_server_port}",
        )

        # Connection parameters
        self._ip = local_server_ip
        self._port = local_server_port

        # Robot data state
        self._robotData: dict[str, Any] = {}
        self._robotConnected: bool = False
        self._cloudConnected: bool = False
        self._serial_number: str | None = None

        # TCP writer for sending commands
        self._writer: asyncio.StreamWriter | None = None

        # Start background task for maintaining connection
        hass.async_create_background_task(self._run(), "CN360-TCP-Task")

        # Notify any initial listeners
        self.async_update_listeners()

    async def _run(self) -> None:
        """Maintain TCP connection, read packets, and update state."""
        while True:
            try:
                _LOGGER.info(
                    "Connecting to CN360 server at %s:%d", self._ip, self._port
                )
                reader, writer = await asyncio.open_connection(self._ip, self._port)
                _LOGGER.info("Connected to CN360 server")

                # Save writer for outgoing commands
                self._writer = writer
                self._robotConnected = True
                self.async_update_listeners()

                while True:
                    # Read packet header
                    header = await reader.readexactly(2)

                    # Data packet: 0x16 0x16
                    if header == b"\x16\x16":
                        # Read length (2 bytes, big endian)
                        length_bytes = await reader.readexactly(2)
                        length = int.from_bytes(length_bytes, "big")
                        payload_bytes = await reader.readexactly(length)

                        try:
                            payload = json.loads(payload_bytes)
                        except json.JSONDecodeError:
                            _LOGGER.warning("Invalid JSON payload: %s", payload_bytes)
                            continue

                        origin = payload.get("origin")
                        if origin == "robot":
                            payload.pop("origin", None)
                            # Update robot data
                            self._serial_number = payload.get("sn", self._serial_number)

                            if (
                                payload.get("robot_connected", self._robotConnected)
                                != self._robotConnected
                            ):
                                self._robotConnected = payload.get(
                                    "robot_connected", self._robotConnected
                                )
                                if self._robotConnected:
                                    await self._request_data()

                            self._cloudConnected = payload.get(
                                "cloud_connected", self._cloudConnected
                            )

                            if (not payload.get("data", None)) and (
                                payload.get("cache", None)
                            ):
                                self._robotData.update(payload.get("cache", {}))
                            else:
                                self._robotData.update(
                                    payload.get("data", {}).get("data", {})
                                )
                            self.async_update_listeners()
                            _LOGGER.info("Robot message: %s", payload)

                        elif origin == "local":
                            self._handle_local_message(payload)

                        elif origin == "server":
                            _LOGGER.info("Server message: %s", payload)
                        else:
                            _LOGGER.debug(
                                "Unknown origin '%s', dropping packet", origin
                            )

                    else:
                        _LOGGER.warning("Unknown packet header: %s", header)
                        await reader.read(1)  # resync

            except asyncio.IncompleteReadError:
                _LOGGER.error("Connection lost to CN360 server, retrying")
            except Exception:
                _LOGGER.exception("Error in CN360 coordinator loop")

            # Clean up writer state
            self._writer = None
            self._robotConnected = False
            self.async_update_listeners()

            # Retry after delay
            await asyncio.sleep(5)

    async def _request_data(self):
        await self.sendCommand(
            30000,
            {
                "mainCmds": ["21014"],
                "cmds": [
                    {"data": {}, "infoType": "21014"},
                    {"data": {}, "infoType": "20001"},
                    {"data": {}, "infoType": "21008"},
                ],
            },
        )
        await self.sendCommand(21034, {})
        await self.sendCommand(
            21011,
            {"startPos": 3, "userId": "35fac39293313047a911b3e210bed1ef", "mask": 0},
        )
        await self.sendCommand(21019, {})

    def _handle_local_message(self, data: dict) -> None:
        """Handle messages from local origin."""
        changed = False
        connected = data.get("connected", False)
        if connected != self._robotConnected:
            self._robotConnected = connected
            changed = True

        self._serial_number = data.get("sn")
        if changed:
            self.async_update_listeners()

    def getRobotData(self) -> dict[str, Any]:
        """Return the latest robot data."""
        return self._robotData.copy()

    def isRobotConnected(self) -> bool:
        """Return True if the robot is currently connected."""
        return self._robotConnected

    def isCloudConnected(self) -> bool:
        """Return True if the cloud is currently connected."""
        return self._cloudConnected

    def getSerialNumber(self) -> str | None:
        """Return Serial Number of Robot."""
        return self._serial_number

    async def sendCommand(self, infoType: int, data: dict[str, Any]) -> None:
        """Send a command packet to the CN360 server."""
        if not self._writer or self._writer.is_closing():
            _LOGGER.error("Cannot send command, not connected to CN360 server")
            return

        # Build payload with origin 'local'
        packet: dict[str, Any] = {
            "origin": "ha",
            "infoType": infoType,
            "sn": self._serial_number,
            "data": data,
        }
        payload_bytes = json.dumps(packet).encode("utf-8")

        try:
            self._writer.write(payload_bytes)
            await self._writer.drain()
            _LOGGER.debug("Sent command: %s", packet)
        except Exception as e:  # noqa: BLE001
            _LOGGER.error("Failed to send command: %s", e)


async def async_setup_coordinator(
    hass: HomeAssistant, entry: ConfigEntry
) -> CN360Coordinator:
    """Set up the CN360 coordinator."""
    return CN360Coordinator(hass, entry.data[CONF_IP], entry.data[CONF_PORT])

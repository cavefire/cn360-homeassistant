"""Camera platform for 360 Robot vacuum."""

from __future__ import annotations

import base64
import io
import logging

from PIL import Image, ImageDraw

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
import homeassistant.util.dt as dt_util

from .const import DOMAIN
from .coordinator import CN360Coordinator

_LOGGER = logging.getLogger(__name__)

# Map drawing constants
MAP_WIDTH = 800
MAP_HEIGHT = 600
MAP_MARGIN = 50
AREA_COLORS = [
    (106, 90, 205, 150),  # Slate blue (semi-transparent)
    (238, 130, 238, 150),  # Violet (semi-transparent)
    (60, 179, 113, 150),  # Medium sea green (semi-transparent)
    (255, 165, 0, 150),  # Orange (semi-transparent)
    (70, 130, 180, 150),  # Steel blue (semi-transparent)
]
BACKGROUND_COLOR = (240, 240, 240, 255)  # Light gray background
OUTLINE_COLOR = (50, 50, 50, 255)  # Dark gray outline
LINE_WIDTH = 2


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up 360 Robot camera based on a config entry."""
    coordinator: CN360Coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    async_add_entities([Robot360MapImage(hass, entry, coordinator)])


class Robot360MapImage(ImageEntity):
    """Camera class for the 360 Robot vacuum map."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        coordinator: CN360Coordinator,
    ) -> None:
        """Initialize the 360 Robot camera."""
        super().__init__(hass)
        self.hass = hass
        self._entry_id = entry.entry_id
        self._attr_unique_id = f"{self._entry_id}_map"
        self._attr_name = "360 Robot Map"
        self._image: bytes | None = None
        self._map_hash: int | None = None
        self._coordinator = coordinator

        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.getSerialNumber())},
        }

        def _update_map_data() -> None:
            """Update the camera image when map data changes."""
            if "smartArea" in self._coordinator.getRobotData():
                self._generate_map_image(self._coordinator.getRobotData())
                self._attr_image_last_updated = dt_util.now()
                self.schedule_update_ha_state()

        self._coordinator.async_add_listener(_update_map_data)

    async def async_update_image_url(self) -> None:
        """Update the image URL if it has changed."""
        value = self.get_native_value()
        if value is None:
            _LOGGER.debug("No image URL found")
        elif isinstance(value, str) and value != self._attr_image_url:
            _LOGGER.debug("Returning updated image URL %s", value)
            self._attr_image_url = value
            self._attr_image_last_updated = dt_util.utcnow()

    async def async_image(self) -> bytes | None:
        """Return a still image from the camera."""
        try:
            # Access data from coordinator to ensure we have the most current data
            if not self._coordinator.getRobotData():
                _LOGGER.debug("No data available from coordinator")
                return self._image

            # Check if we have map data
            if "smartArea" not in self._coordinator.getRobotData():
                _LOGGER.debug("No map data available")
                return self._image

            # Get the current map data
            map_data = self._coordinator.getRobotData().get("smartArea", {})

            # Calculate a hash value of the map data to detect changes
            current_hash = hash(str(map_data))

            # Only regenerate the image if the map data has changed
            # if self._map_hash != current_hash or self._image is None or True:
            self._map_hash = current_hash
            self._image = await self.hass.async_add_executor_job(
                self._generate_map_image, map_data
            )
            _LOGGER.debug("Generated new map image")

            return self._image
        except Exception as err:
            _LOGGER.debug("Error getting camera image: %s", err)
            return None

    @property
    def extra_state_attributes(self):
        return {"data": self._coordinator.getRobotData().get("smartArea", {})}

    def _generate_map_image(self, map_data: dict) -> bytes:
        """Generate the map image from the map data."""
        # Create a new image with a white background
        img = Image.new("RGBA", (MAP_WIDTH, MAP_HEIGHT), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)

        # Get the vertexes from the map data
        areas = map_data.get("value", [])
        if not areas:
            # If no areas, return a blank image
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()

        # Find the bounds of all vertices to center the map
        all_vertices = []
        for area in areas:
            vertices = area.get("vertexs", [])
            all_vertices.extend(vertices)

        if not all_vertices:
            # If no vertices, return a blank image
            buffer = io.BytesIO()
            img.save(buffer, format="PNG")
            return buffer.getvalue()

        # Determine min and max x,y values to scale the map properly
        min_x = min(point[0] for point in all_vertices)
        max_x = max(point[0] for point in all_vertices)
        min_y = min(point[1] for point in all_vertices)
        max_y = max(point[1] for point in all_vertices)

        # Add a little margin
        min_x = min_x - MAP_MARGIN
        max_x = max_x + MAP_MARGIN
        min_y = min_y - MAP_MARGIN
        max_y = max_y + MAP_MARGIN

        # Calculate scaling factors
        width = max_x - min_x
        height = max_y - min_y

        # Avoid division by zero
        if width == 0:
            width = 1
        if height == 0:
            height = 1

        scale_x = (MAP_WIDTH - 2 * MAP_MARGIN) / width
        scale_y = (MAP_HEIGHT - 2 * MAP_MARGIN) / height

        # Use the smaller scaling factor to maintain aspect ratio
        scale = min(scale_x, scale_y)

        # Draw each area with a different color
        for i, area in enumerate(areas):
            vertices = area.get("vertexs", [])
            if not vertices:
                continue

            # Scale and transform vertices
            scaled_vertices = []
            for x, y in vertices:
                # Flip Y coordinate (PIL uses top-left as origin)
                # Note: Negating y to flip the coordinate system
                scaled_x = (x - min_x) * scale + MAP_MARGIN
                scaled_y = MAP_HEIGHT - ((y - min_y) * scale + MAP_MARGIN)
                scaled_vertices.append((scaled_x, scaled_y))

            # Get a color for this area (cycle through predefined colors)
            color = AREA_COLORS[i % len(AREA_COLORS)]

            # Draw the filled polygon
            draw.polygon(
                scaled_vertices, fill=color, outline=OUTLINE_COLOR, width=LINE_WIDTH
            )

            # Draw area name if available
            name = area.get("name", "")
            if name:
                try:
                    # Names are base64 encoded
                    decoded_name = base64.b64decode(name).decode("utf-8")

                    # Find center of the area
                    center_x = sum(v[0] for v in scaled_vertices) / len(scaled_vertices)
                    center_y = sum(v[1] for v in scaled_vertices) / len(scaled_vertices)

                    # Draw the text
                    if area.get("id", -1) in self._coordinator.getRobotData().get(
                        "smartArea"
                    ).get("activeIds", []):
                        draw.text(
                            (center_x, center_y), decoded_name, fill=(255, 0, 0, 255)
                        )
                    else:
                        draw.text(
                            (center_x, center_y), decoded_name, fill=(0, 0, 0, 255)
                        )

                except Exception:
                    pass

        timeStr = dt_util.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        draw.text((10, 10), timeStr, fill=(0, 0, 0, 255))

        # If we have the robot's current position, draw it as a dot
        pos = self._coordinator.getRobotData().get("pos")
        if pos and isinstance(pos, list) and len(pos) == 2:
            try:
                robot_x, robot_y = pos
                # Scale and transform position
                scaled_x = (robot_x - min_x) * scale + MAP_MARGIN
                scaled_y = MAP_HEIGHT - ((robot_y - min_y) * scale + MAP_MARGIN)

                # Draw a red dot for the robot
                robot_radius = 5
                draw.ellipse(
                    (
                        scaled_x - robot_radius,
                        scaled_y - robot_radius,
                        scaled_x + robot_radius,
                        scaled_y + robot_radius,
                    ),
                    fill=(255, 0, 0, 255),  # Red
                    outline=(0, 0, 0, 255),  # Black outline
                )
            except Exception as err:
                _LOGGER.debug("Error drawing robot position: %s", err)

        # Convert the image to bytes
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")

        # print base64 image
        base64_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        _LOGGER.debug("Base64 image: %s", base64_image)

        return buffer.getvalue()

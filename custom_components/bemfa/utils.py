"""Support for bemfa service."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant

_LOGGING = logging.getLogger(__name__)


def has_key(data: Any, key: str) -> bool:
    """Whether data has specific valid key."""
    return key in data and data[key] is not None


def get_area_entities(hass: HomeAssistant, area_id: str) -> list[str]:
    """Get all entity IDs that belong to a specific area."""
    from homeassistant.helpers import entity_registry  # Lazy import to avoid blocking

    try:
        registry = entity_registry.async_get(hass)
        return [
            entry.entity_id
            for entry in registry.entities.values()
            if entry.area_id == area_id
        ]
    except (AttributeError, RuntimeError):
        _LOGGING.warning("Failed to retrieve entities for area %s", area_id)
        return []

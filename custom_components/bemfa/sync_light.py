"""Support for bemfa service."""
from __future__ import annotations

from collections.abc import Mapping, Callable
from typing import Any
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_BRIGHTNESS_PCT,
    ATTR_RGB_COLOR,
    ATTR_SUPPORTED_COLOR_MODES,
    DOMAIN,
    ColorMode,
)
from homeassistant.const import SERVICE_TURN_OFF, SERVICE_TURN_ON, STATE_ON
from homeassistant.util.read_only_dict import ReadOnlyDict
from .const import MSG_OFF, MSG_ON, TopicSuffix
from .utils import has_key
from .sync import SYNC_TYPES, ControllableSync


@SYNC_TYPES.register("light")
class Light(ControllableSync):
    """Sync a hass light entity to bemfa light device."""

    @staticmethod
    def get_config_step_id() -> str:
        return "sync_config_light"

    @staticmethod
    def _get_topic_suffix() -> TopicSuffix:
        return TopicSuffix.LIGHT

    @staticmethod
    def _supported_domain() -> str:
        return DOMAIN

    def _msg_generators(
        self,
    ) -> list[Callable[[str, ReadOnlyDict[Mapping[str, Any]]], str | int]]:
        attr_color_temp_kelvin = "color_temp_kelvin"
        attr_color_temp_mired = "color_temp"
        return [
            lambda state, attributes: MSG_ON if state == STATE_ON else MSG_OFF,
            lambda state, attributes: round(attributes[ATTR_BRIGHTNESS] / 2.55)
            if has_key(attributes, ATTR_BRIGHTNESS)
            else "",
            lambda state, attributes: attributes[attr_color_temp_kelvin]
            if has_key(attributes, attr_color_temp_kelvin)
            else 1000000 // attributes[attr_color_temp_mired]
            if has_key(attributes, attr_color_temp_mired)
            else attributes[ATTR_RGB_COLOR][0] * 256 * 256
            + attributes[ATTR_RGB_COLOR][1] * 256
            + attributes[ATTR_RGB_COLOR][2]
            if has_key(attributes, ATTR_RGB_COLOR)
            else "",
        ]

    def _msg_resolvers(
        self,
    ) -> list[
        (
            int,
            int,
            Callable[
                [list[str | int], ReadOnlyDict[Mapping[str, Any]]],
                (str, str, dict[str, Any]),
            ],
        )
    ]:
        attr_color_temp_kelvin = "color_temp_kelvin"
        attr_min_color_temp_kelvin = "min_color_temp_kelvin"
        attr_max_color_temp_kelvin = "max_color_temp_kelvin"
        attr_color_temp_mired = "color_temp"
        attr_min_mireds = "min_mireds"
        attr_max_mireds = "max_mireds"
        return [
            (
                0,
                3,
                lambda msg, attributes: (
                    DOMAIN,
                    SERVICE_TURN_ON if msg[0] == MSG_ON else SERVICE_TURN_OFF,
                    {
                        ATTR_BRIGHTNESS_PCT: msg[1],
                        **(
                            {
                                attr_color_temp_kelvin: min(
                                    max(
                                        int(msg[2]),
                                        attributes[attr_min_color_temp_kelvin],
                                    ),
                                    attributes[attr_max_color_temp_kelvin],
                                )
                            }
                            if has_key(attributes, attr_min_color_temp_kelvin)
                            and has_key(attributes, attr_max_color_temp_kelvin)
                            else {
                                attr_color_temp_mired: min(
                                    max(
                                        1000000 // int(msg[2]),
                                        attributes[attr_min_mireds],
                                    ),
                                    attributes[attr_max_mireds],
                                )
                            }
                        ),
                    }
                    if len(msg) > 2
                    and has_key(attributes, ATTR_SUPPORTED_COLOR_MODES)
                    and ColorMode.COLOR_TEMP in attributes[ATTR_SUPPORTED_COLOR_MODES]
                    else {
                        ATTR_BRIGHTNESS_PCT: msg[1],
                        ATTR_RGB_COLOR: [
                            msg[2] // 256 // 256,
                            msg[2] // 256 % 256,
                            msg[2] % 256,
                        ],
                    }
                    if len(msg) > 2
                    else {ATTR_BRIGHTNESS_PCT: msg[1]}
                    if len(msg) > 1
                    else {},
                ),
            )
        ]

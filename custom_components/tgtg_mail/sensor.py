"""Sensoren für Too Good To Go Mail."""
from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TgtgConfigEntry
from .entity import TgtgEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: TgtgConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    c = entry.runtime_data
    async_add_entities([NaechsteAbholung(c), OffeneAbholungen(c)])


class NaechsteAbholung(TgtgEntity, SensorEntity):
    _attr_name = "Nächste Abholung"
    _attr_icon = "mdi:shopping-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "naechste_abholung")

    @property
    def native_value(self):
        return self.coordinator.data[0].start if self.coordinator.data else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        daten = self.coordinator.data or []
        attrs: dict[str, Any] = {"bestellungen": [b.as_dict() for b in daten]}
        if daten:
            b = daten[0]
            attrs.update(b.as_dict())
            attrs["ende"] = b.ende.isoformat()
            attrs["stornieren_bis"] = (b.start - timedelta(hours=2)).isoformat()
        return attrs


class OffeneAbholungen(TgtgEntity, SensorEntity):
    _attr_name = "Offene Abholungen"
    _attr_icon = "mdi:basket-outline"
    _attr_native_unit_of_measurement = "Tüten"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "offene_abholungen")

    @property
    def native_value(self) -> int:
        return len(self.coordinator.data or [])

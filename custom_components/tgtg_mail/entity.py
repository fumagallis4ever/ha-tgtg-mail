"""Basis-Entität."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import TgtgCoordinator


class TgtgEntity(CoordinatorEntity[TgtgCoordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: TgtgCoordinator, key: str) -> None:
        super().__init__(coordinator)
        eid = coordinator.config_entry.entry_id
        self._attr_unique_id = f"{eid}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, eid)},
            name="Too Good To Go",
            manufacturer="Too Good To Go",
            model="E-Mail-Auswertung",
            entry_type=DeviceEntryType.SERVICE,
        )

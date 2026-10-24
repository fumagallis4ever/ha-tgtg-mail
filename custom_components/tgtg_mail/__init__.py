"""Too Good To Go Mail – Abholungen aus dem Postfach."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .coordinator import TgtgCoordinator

PLATFORMS = [Platform.SENSOR, Platform.CALENDAR]

type TgtgConfigEntry = ConfigEntry[TgtgCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: TgtgConfigEntry) -> bool:
    coordinator = TgtgCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_neu_laden))
    return True


async def _neu_laden(hass: HomeAssistant, entry: TgtgConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: TgtgConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

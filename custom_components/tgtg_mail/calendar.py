"""Kalender mit allen Abholungen."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TgtgConfigEntry
from .entity import TgtgEntity
from .parser import Bestellung


async def async_setup_entry(
    hass: HomeAssistant, entry: TgtgConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    async_add_entities([TgtgKalender(entry.runtime_data)])


def _event(b: Bestellung) -> CalendarEvent:
    beschreibung = f"Bestell-ID: {b.bestell_id}\nAnzahl: {b.anzahl}"
    if b.preis:
        beschreibung += f"\nPreis: {b.preis}"
    return CalendarEvent(
        start=b.start, end=b.ende,
        summary=f"TGTG: {b.geschaeft}",
        location=b.adresse, description=beschreibung, uid=b.bestell_id,
    )


class TgtgKalender(TgtgEntity, CalendarEntity):
    _attr_name = "Abholungen"
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "kalender")

    @property
    def event(self) -> CalendarEvent | None:
        daten = self.coordinator.data
        return _event(daten[0]) if daten else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return [
            _event(b) for b in self.coordinator.alle
            if not b.storniert and b.ende > start_date and b.start < end_date
        ]

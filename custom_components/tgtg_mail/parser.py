"""Parser für Too-Good-To-Go-Bestätigungsmails."""
from __future__ import annotations

import html
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Europe/Berlin")

MONATE = {
    "januar": 1, "februar": 2, "märz": 3, "maerz": 3, "april": 4, "mai": 5,
    "juni": 6, "juli": 7, "august": 8, "september": 9, "oktober": 10,
    "november": 11, "dezember": 12,
}


@dataclass
class Bestellung:
    bestell_id: str
    geschaeft: str
    adresse: str | None
    start: datetime
    ende: datetime
    anzahl: int = 1
    preis: str | None = None
    storniert: bool = False
    mail_datum: datetime | None = field(default=None, compare=False)

    def as_dict(self) -> dict:
        return {
            "bestell_id": self.bestell_id,
            "geschaeft": self.geschaeft,
            "adresse": self.adresse,
            "start": self.start.isoformat(),
            "ende": self.ende.isoformat(),
            "abholzeit": f"{self.start:%H:%M} – {self.ende:%H:%M}",
            "datum": f"{self.start:%d.%m.%Y}",
            "anzahl": self.anzahl,
            "preis": self.preis,
        }


def html_zu_text(raw: str) -> str:
    """HTML grob in Text umwandeln (eine Zeile pro Block)."""
    txt = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    txt = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|td|li|h\d|table)>", "\n", txt)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = html.unescape(txt).replace("\xa0", " ")
    zeilen = [re.sub(r"[ \t]+", " ", z).strip() for z in txt.splitlines()]
    return "\n".join(z for z in zeilen if z)


def _feld(text: str, name: str) -> str | None:
    m = re.search(rf"{name}\s*:\s*(.+?)(?:\n|$)", text)
    return m.group(1).strip() if m else None


def parse_bestaetigung(text: str) -> Bestellung | None:
    """Bestellbestätigung auslesen. Gibt None zurück, wenn es keine ist."""
    flat = re.sub(r"\s+", " ", text)

    bid = _feld(text, "Bestell-ID")
    if not bid:
        return None
    bid = bid.split()[0]

    m = re.search(r"Bestellung bei (.+?)!", flat)
    geschaeft = m.group(1).strip() if m else "Too Good To Go"

    # Datum: "Samstag, 24. Oktober 2026"
    m = re.search(r"Datum\s*:\s*\w+,\s*(\d{1,2})\.\s*([A-Za-zäÄ]+)\s+(\d{4})", flat)
    if not m:
        return None
    tag, monat_txt, jahr = int(m.group(1)), m.group(2).lower(), int(m.group(3))
    monat = MONATE.get(monat_txt)
    if not monat:
        return None

    # Abholzeit: "19:30 - 20:00"
    m = re.search(r"Abholzeit\s*:\s*(\d{1,2}):(\d{2})\s*[-–]\s*(\d{1,2}):(\d{2})", flat)
    if not m:
        return None
    h1, m1, h2, m2 = (int(x) for x in m.groups())
    start = datetime(jahr, monat, tag, h1, m1, tzinfo=TZ)
    ende = datetime(jahr, monat, tag, h2, m2, tzinfo=TZ)
    if ende <= start:  # Abholung über Mitternacht
        ende += timedelta(days=1)

    m = re.search(r"Standort\s*:\s*(.+?)\s*(?:\(\s*In Karten|Bestell-ID)", flat)
    adresse = m.group(1).strip().rstrip(",") if m else None

    anzahl = 1
    a = _feld(text, "Anzahl")
    if a and a.split()[0].isdigit():
        anzahl = int(a.split()[0])

    m = re.search(r"Gesamtpreis\s*:\s*([\d.,]+\s*€)", flat)
    preis = m.group(1) if m else None

    return Bestellung(bid, geschaeft, adresse, start, ende, anzahl, preis)


def parse_stornierung(text: str) -> str | None:
    """Bestell-ID einer Stornierungsmail zurückgeben, sonst None."""
    if not re.search(r"storniert|Stornierung", text, re.I):
        return None
    if re.search(r"Bestellung bei .+?!", text) and "Abholzeit" in text:
        # Normale Bestätigung, die nur auf Stornierung hinweist
        if not re.search(r"wurde storniert|ist storniert|Stornierung (deiner|bestätigt)", text, re.I):
            return None
    bid = _feld(text, "Bestell-ID")
    return bid.split()[0] if bid else None

"""Ruft TGTG-Mails per IMAP ab und hält die offenen Abholungen."""
from __future__ import annotations

import email
import imaplib
import logging
from datetime import datetime, timedelta
from email.header import decode_header, make_header

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DAYS, CONF_FOLDER, CONF_SENDER, DEFAULT_DAYS, DEFAULT_FOLDER,
    DEFAULT_SENDER, DOMAIN, SCAN_INTERVAL_MINUTES,
)
from .parser import Bestellung, html_zu_text, parse_bestaetigung, parse_stornierung

_LOGGER = logging.getLogger(__name__)


class ImapLoginError(Exception):
    """Anmeldung fehlgeschlagen."""


def imap_verbinden(host: str, port: int, user: str, pw: str) -> imaplib.IMAP4_SSL:
    conn = imaplib.IMAP4_SSL(host, port, timeout=30)
    try:
        conn.login(user, pw)
    except imaplib.IMAP4.error as err:
        raise ImapLoginError(str(err)) from err
    return conn


def _mail_text(msg: email.message.Message) -> str:
    html_teil, text_teil = None, None
    for part in msg.walk():
        ctype = part.get_content_type()
        if part.get_content_disposition() == "attachment":
            continue
        if ctype in ("text/html", "text/plain"):
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            charset = part.get_content_charset() or "utf-8"
            inhalt = payload.decode(charset, errors="replace")
            if ctype == "text/html" and html_teil is None:
                html_teil = inhalt
            elif ctype == "text/plain" and text_teil is None:
                text_teil = inhalt
    if html_teil:
        return html_zu_text(html_teil)
    return text_teil or ""


class TgtgCoordinator(DataUpdateCoordinator[list[Bestellung]]):
    """Koordinator für Too-Good-To-Go-Abholungen."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN, config_entry=entry,
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )
        self.entry = entry
        self.alle: list[Bestellung] = []

    def _abrufen(self) -> list[Bestellung]:
        d = {**self.entry.data, **self.entry.options}
        tage = int(d.get(CONF_DAYS, DEFAULT_DAYS))
        absender = d.get(CONF_SENDER, DEFAULT_SENDER)
        conn = imap_verbinden(d[CONF_HOST], d[CONF_PORT], d[CONF_USERNAME], d[CONF_PASSWORD])
        try:
            status, _ = conn.select(f'"{d.get(CONF_FOLDER, DEFAULT_FOLDER)}"', readonly=True)
            if status != "OK":
                raise UpdateFailed("Ordner nicht gefunden")
            d0 = datetime.now() - timedelta(days=tage)
            mon = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()[d0.month - 1]
            seit = f"{d0.day:02d}-{mon}-{d0.year}"  # IMAP braucht englische Monatsnamen
            status, daten = conn.search(None, "FROM", f'"{absender}"', "SINCE", seit)
            if status != "OK":
                raise UpdateFailed("IMAP-Suche fehlgeschlagen")
            bestellungen: dict[str, Bestellung] = {}
            stornos: set[str] = set()
            for num in daten[0].split():
                status, teile = conn.fetch(num, "(BODY.PEEK[])")
                if status != "OK" or not teile or not isinstance(teile[0], tuple):
                    continue
                msg = email.message_from_bytes(teile[0][1])
                betreff = str(make_header(decode_header(msg.get("Subject", ""))))
                text = _mail_text(msg)
                bid = parse_stornierung(f"{betreff}\n{text}")
                if bid:
                    stornos.add(bid)
                    continue
                b = parse_bestaetigung(text)
                if b:
                    bestellungen[b.bestell_id] = b
        finally:
            try:
                conn.logout()
            except Exception:  # noqa: BLE001
                pass
        for bid in stornos:
            if bid in bestellungen:
                bestellungen[bid].storniert = True
        return sorted(bestellungen.values(), key=lambda b: b.start)

    async def _async_update_data(self) -> list[Bestellung]:
        try:
            self.alle = await self.hass.async_add_executor_job(self._abrufen)
        except ImapLoginError as err:
            raise ConfigEntryAuthFailed(err) from err
        except (OSError, imaplib.IMAP4.error) as err:
            raise UpdateFailed(f"IMAP-Fehler: {err}") from err
        jetzt = dt_util.now()
        return [b for b in self.alle if not b.storniert and b.ende > jetzt]

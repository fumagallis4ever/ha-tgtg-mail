# Too Good To Go Mail

Home-Assistant-Integration, die deine Too-Good-To-Go-Bestellbestätigungen per IMAP aus dem Postfach liest und als Sensoren und Kalender bereitstellt – ohne die inoffizielle TGTG-API.

[![Open HACS Repository on My Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=fumagallis4ever&repository=ha-tgtg-mail&category=integration)
[![Add Integration to My Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=tgtg_mail)

## Installation über HACS

1. Oben auf **„Open HACS Repository on My“** klicken (oder in HACS → ⋮ → *Benutzerdefinierte Repositories* → `https://github.com/fumagallis4ever/ha-tgtg-mail`, Typ *Integration*).
2. **Herunterladen** und Home Assistant neu starten.
3. Auf **„Add Integration to My“** klicken und IMAP-Zugang eintragen (IONOS: `imap.ionos.de`, Port `993`).

## Entitäten

| Entität | Inhalt |
|---|---|
| `sensor.too_good_to_go_nachste_abholung` | Startzeit der nächsten Abholung, Attribute: Geschäft, Adresse, Abholzeit, Bestell-ID, Anzahl, Preis, Stornieren bis, Liste aller offenen Bestellungen |
| `sensor.too_good_to_go_offene_abholungen` | Anzahl offener Abholungen |
| `calendar.too_good_to_go_abholungen` | Alle Abholungen als Kalendertermine |

## Funktionsweise

- Abruf alle 5 Minuten, nur lesend (Mails bleiben ungelesen).
- Durchsucht Mails der letzten 14 Tage vom Absender `toogoodtogo` (in den Optionen änderbar).
- Stornierte Bestellungen werden ausgeblendet, abgelaufene Abholfenster verschwinden automatisch.

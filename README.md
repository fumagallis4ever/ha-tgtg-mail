# Too Good To Go Mail

Home-Assistant-Integration, die deine Too-Good-To-Go-Bestellbestätigungen per IMAP aus dem Postfach liest und als Sensoren und Kalender bereitstellt – ohne die inoffizielle TGTG-API.

[![Open HACS Repository on My Home Assistant](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=fumagallis4ever&repository=ha-tgtg-mail&category=integration)
[![Add Integration to My Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=tgtg_mail)

## Warum E-Mail statt API?

Too Good To Go bietet keine offizielle API. Bestehende Integrationen nutzen die inoffizielle App-Schnittstelle – das hat einige Nachteile, die der Weg über das Postfach vermeidet:

| | Inoffizielle API | E-Mail (diese Integration) |
|---|---|---|
| **Stabilität** | Kann sich jederzeit ändern und Integrationen lahmlegen | Ändert sich das Mail-Layout, muss nur der Parser angepasst werden |
| **Sperrgefahr** | Zu häufige Abfragen führen zu Sperren durch TGTG | Keine Anfragen an TGTG – nur das eigene Postfach wird gelesen |
| **Captcha / Login** | Login per PIN, teils Captcha („Additional verification required“), Tokens laufen ab | Einmalig IMAP-Zugang eintragen, fertig |
| **Abdeckung** | Nur Favoriten-Shops (oder manuell eingetragene IDs) | Jede Bestellung, egal bei welchem Shop |
| **Datenschutz** | Zugriff auf das komplette TGTG-Konto | Liest nur Mails vom Absender `toogoodtogo`, rein lesend (Mails bleiben ungelesen) |

Einziger Nachteil: Die Integration kennt nur Bestellungen, keine verfügbaren Überraschungstüten. Wer über neue Tüten bei Favoriten benachrichtigt werden möchte, braucht weiterhin die API-Variante.

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

## Dashboard-Kachel

Markdown-Karte, die nur erscheint, wenn eine Abholung offen ist. Im Dashboard „Karte hinzufügen“ → *Manuell* und folgenden Code einfügen:

```yaml
type: markdown
title: 🥐 Too Good To Go
visibility:
  - condition: numeric_state
    entity: sensor.too_good_to_go_offene_abholungen
    above: 0
content: >-
  {% for b in state_attr('sensor.too_good_to_go_nachste_abholung', 'bestellungen') or [] %}
  **{{ b.geschaeft }}**  
  📅 {{ 'Heute' if b.datum == now().strftime('%d.%m.%Y') else b.datum }}, {{ b.abholzeit }} Uhr  
  📍 {{ b.adresse }}  
  🛍️ {{ b.anzahl }}×
  {% if not loop.last %}<hr>{% endif %}
  {% endfor %}
```

Wer den Preis anzeigen möchte, ergänzt hinter `{{ b.anzahl }}×` noch ` · {{ b.preis }}`.

## Funktionsweise

- Abruf alle 5 Minuten, nur lesend (Mails bleiben ungelesen).
- Durchsucht Mails der letzten 14 Tage vom Absender `toogoodtogo` (in den Optionen änderbar).
- Stornierte Bestellungen werden ausgeblendet, abgelaufene Abholfenster verschwinden automatisch.

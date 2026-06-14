---
name: listonic-lists
description: 'Odczyt list zakupów Listonic — pokazuje listy, pozycje, status odhaczenia. Wyzwalacze: "co mam na liście zakupów", "pokaż listonic", "co zostało do kupienia", "co już odhaczone".'
---

# listonic-lists

- Wszystko: `listonic lists --json`
- Do kupienia: `listonic lists --unchecked --json`
- Już odhaczone: `listonic lists --checked --json`

Parsuj JSON i przedstaw czytelnie (per lista, pozycje). Brak konfiguracji → skieruj do skilla listonic-setup.

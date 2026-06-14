---
name: listonic-edit
description: 'Zapis na listach Listonic — dodaj pozycję, odhacz, cofnij odhaczenie, usuń. Wyzwalacze: "dodaj do listy zakupów", "odhacz na listonic", "usuń z listy", "kupiłem X".'
---

# listonic-edit

- Dodaj: `listonic add "<lista>" "<pozycja>"`
- Odhacz: `listonic check "<lista>" "<pozycja>"`
- Cofnij: `listonic check "<lista>" "<pozycja>" --uncheck`
- Usuń: `listonic remove "<lista>" "<pozycja>"`

## Zasady
- **Potwierdź z użytkownikiem przed każdą operacją zapisu** (modyfikuje realną listę).
- Nazwy list/pozycji dopasowywane bez względu na wielkość liter; gdy brak — zgłoś czytelnie.

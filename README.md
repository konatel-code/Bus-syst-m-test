# Stav aplikácií - týždenný monitoring repozitárov konatel-code

Nástroj, ktorý každý pondelok zozbiera stav všetkých repozitárov (commity, vetvy, PR, CI, README), porovná ho
s minulým týždňom a vygeneruje HTML report pre Davida Gavaľu.

- `tools/collect.py OUT.json` - zber dát cez `gh api` (repozitáre musia byť pripojené v relácii cez add_repo)
- `tools/report.py` - generuje HTML z `repos.json` + `assessment.json` (ručné/AI hodnotenie stavu každého projektu)
- `state/assessment.json` - hodnotenie z posledného behu: kategória (`kat`), stav, na čo sa čaká, ďalší krok
- `state/last_snapshot.json` - zjednodušený snímok z posledného behu na porovnanie (push, commity, PR, CI)
- `reports/` - vygenerované reporty podľa dátumu

Kategórie: AKTIVNY (commity za 7 dní), AUTO (beží automaticky), CAKA_TEBA (hotové v PR, čaká na rozhodnutie/nasadenie),
NASADENE (zlúčené, bez aktivity 30+ dní), ZAMRZNUTE (dlhšie bez pohybu, nejasné pokračovanie), PRAZDNE.

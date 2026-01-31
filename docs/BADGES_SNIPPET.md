Badges CI (snippet à coller en haut de README.md)

Si tes workflows s'appellent bien:
- ci.yml
- test.yml
- collect-stable.yml
- mass-collect.yml

Alors tu peux coller:

![ci](../../actions/workflows/ci.yml/badge.svg?branch=main)
![tests](../../actions/workflows/test.yml/badge.svg?branch=main)
![collect-stable](../../actions/workflows/collect-stable.yml/badge.svg?branch=main)
![mass-collect](../../actions/workflows/mass-collect.yml/badge.svg?branch=main)

Si un nom de workflow diffère, remplace le nom de fichier dans l'URL.

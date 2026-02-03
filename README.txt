Mise à jour BareFlux — correctif CI

Problème observé:
  - Le workflow .github/workflows/collect-stable.yml exécute:
      pip install ... -c constraints.txt
    et échoue si constraints.txt n'existe pas.

Correctif minimal:
  1) Dézipper ce fichier à la racine du repo BareFlux
  2) Commit + push

Effet:
  - constraints.txt existe, donc le job "collect" ne casse plus sur "Could not open requirements file: constraints.txt".

Optionnel:
  - Pour un pinning réel, remplace les commentaires par des versions exactes.

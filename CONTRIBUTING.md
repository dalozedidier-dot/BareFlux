# Comment contribuer à [Nom du dépôt – ex. BareFlux]

Ce projet est un prototype philosophique et expérimental. Toute contribution est bienvenue, même minime.

## Processus recommandé

1. Fork le dépôt
2. Crée une branche descriptive : `git checkout -b feat/nouvelle-observation` ou `fix/bug-tests-python312`
3. Fais tes modifications
4. Lance les tests localement :
   ```bash
   pytest tests/ --cov
   ./run_modules.sh   # pour BareFlux

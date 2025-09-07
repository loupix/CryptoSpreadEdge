# CI - Exécution des tests

## Workflow

- Fichier: `.github/workflows/tests.yml`
- Sur Pull Request:
  - Exécute `tests/unit`
  - Exécute `tests/integration`
- Sur `main`:
  - Exécute `tests/e2e`
  - Filtre pour ignorer les suites lourdes (deep learning/prediction) non nécessaires

## Dépendances lourdes

- Certains tests (ex: deep learning, prédiction) nécessitent `torch` ou `ta-lib`.
- Par défaut, ces dépendances ne sont pas installées en CI.
- Vous pouvez filtrer:

```bash
pytest -k "not deep_learning and not prediction"
```

## Local

- Unitaires:
```bash
pytest tests/unit
```
- Intégration:
```bash
pytest tests/integration
```
- E2E:
```bash
pytest tests/e2e
```

## Conseils

- Ajoutez de nouveaux tests unitaires à `tests/unit`.
- Pour des scénarios multi-modules, préférez `tests/integration`.
- Les tests E2E doivent rester rapides et stables (smoke + flux critique).
# Lancer les tests unitaires en local

Les tests unitaires de l'API se trouvent dans le dossier `tests/`.
Ils utilisent `pytest` et une base SQLite temporaire en mémoire grâce aux fixtures du fichier `tests/conftest.py`.


## 1. Lancer tous les tests

```bash
python -m pytest tests -q
```

L'option `-q` affiche un résultat compact.

Vous pouvez aussi utiliser la commande complète :

```bash
pytest tests -q
```

## 2. Lancer uniquement les tests des commandes

```bash
python -m pytest tests/test_orders.py -q
```

## 3. Lancer uniquement les tests de l'API

```bash
python -m pytest tests/test_api.py -q
```

## 4. Obtenir plus de détails

Pour afficher le nom de chaque test exécuté :

```bash
python -m pytest tests -v
```

Pour arrêter l'exécution à la première erreur :

```bash
python -m pytest tests -x
```

Pour relancer uniquement les tests échoués lors de la dernière exécution :

```bash
python -m pytest tests --lf
```


## Remarque

Il n'est pas nécessaire de démarrer le serveur Flask avec `python -m app.main` pour exécuter les tests `pytest`.
Les fixtures créent directement une application de test et un client HTTP de test.

La base de données de test est temporaire et ne modifie pas la base locale `digimarket.db`.

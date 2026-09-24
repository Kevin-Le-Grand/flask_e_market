# flask_e_market

API REST de marketplace développée avec Flask, SQLAlchemy, SQLite et JWT.

## Installation depuis GitHub

### Prérequis

- Git
- Python 3.10 ou une version plus récente
- `pip`

### 1. Cloner le dépôt

```bash
git clone https://github.com/Kevin-Le-Grand/flask_e_market.git
cd flask_e_market
```

### 2. Créer un environnement virtuel

Sur Linux ou macOS :

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Sur Windows PowerShell :

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Installer les dépendances

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 4. Configurer la clé JWT

L'application nécessite une variable `JWT_SECRET_KEY`. Créez un fichier `.env`
dans le dossier racine du projet, au même niveau que `requirements.txt` :

Vous pouvez générer une clé en exécutant ce scrip :
```
import secrets

print(secrets.token_hex(32))
```

Puis stocker la clé dans le .env

```dotenv
JWT_SECRET_KEY=remplacez-cette-valeur-par-la-cle-generee
```

Utilisez une valeur longue et aléatoire en dehors d'un environnement de test.
Ne publiez jamais votre fichier `.env` ni sa clé secrète sur GitHub.

### 5. Lancer l'API

Avec l'environnement virtuel activé :

```bash
python -m app.main
```

L'API est alors accessible à l'adresse suivante :

```text
http://127.0.0.1:5000
```

Pour vérifier que le serveur fonctionne, ouvrez :

```text
http://127.0.0.1:5000/health
```

La réponse attendue est :

```json
{"status": "ok"}
```

Le serveur est lancé en mode debug par la commande ci-dessus. Ce mode est
réservé au développement local et ne doit pas être utilisé en production.

## Base de données

L'application utilise une base SQLite nommée `digimarket.db`, créée dans le
dossier racine du projet lorsque la base est initialisée. Les données locales
ne doivent pas être publiées sur GitHub.

## Fonctionnalités

- Création de compte et authentification par JWT
- Gestion des produits
- Gestion des commandes
- Contrôle d'accès pour les administrateurs
- Vérification de l'état de l'API avec `/health`

## Principales routes

| Méthode | Route | Description | Authentification |
| --- | --- | --- | --- |
| `GET` | `/health` | Vérifier l'état de l'API | Non |
| `POST` | `/api/auth/register` | Créer un compte | Non |
| `POST` | `/api/auth/login` | Se connecter et obtenir un JWT | Non |
| `GET` | `/api/produits` | Lister les produits | JWT |
| `GET` | `/api/produits/<id>` | Consulter un produit | JWT |
| `POST` | `/api/produits` | Créer un produit | Admin |
| `GET` | `/api/commandes` | Lister les commandes | JWT |
| `GET` | `/api/commandes/<id>` | Consulter une commande | JWT |
| `POST` | `/api/commandes` | Créer une commande | JWT |

Après une connexion, envoyez le jeton reçu dans l'en-tête HTTP suivant :

```text
Authorization: Bearer <votre_token>
```

## Arrêter l'environnement virtuel

```bash
deactivate
```

## Exécuter les tests

Les tests utilisent une base SQLite temporaire en mémoire et ne modifient pas
la base locale `digimarket.db` :

```bash
python -m pytest -q
```

Une GitHub Action exécute automatiquement ces tests à chaque `push` sur le
dépôt. La variable `JWT_SECRET_KEY` de la CI est fournie par le workflow et
 ne nécessite aucune configuration supplémentaire.


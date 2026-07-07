# Académie de Sorcellerie — squelette de départ

Ceci est un point de départ, pas une base à compléter à l'identique : la structure des fichiers reste entre vos mains, comme le précise le cahier des charges. Ce squelette pose juste trois choses qui seraient fastidieuses à mettre en place vous-mêmes en début de jour 1 : l'app factory Flask, la connexion SQLAlchemy, et un premier test qui prouve que tout ça démarre.

Le README complet (installation, variables d'environnement, seed, tests) attendu en livrable du jour 4 est à écrire par vous-même au fil du projet — celui-ci ne couvre que la mise en route de ce squelette.

## Structure

```
.
├── app/
│   ├── __init__.py       # create_app() : app factory, enregistre les blueprints
│   ├── extensions.py     # instance unique de SQLAlchemy (db)
│   ├── models/
│   │   └── __init__.py   # TimestampMixin ; un module par entité à ajouter ici
│   └── routes/
│       └── health.py     # exemple de blueprint, GET /health
├── tests/
│   ├── conftest.py       # fixtures app / client (base en mémoire)
│   └── test_health.py
├── config.py             # Config (dev) / TestingConfig
├── run.py                # lance le serveur de développement
├── seed.py               # point d'entrée du script de seed, à compléter
├── requirements.txt
└── .env.example
```

Pourquoi une app factory plutôt qu'un fichier unique : le projet grossit vite (une dizaine de ressources sur 4 jours), et l'app factory permet de faire tourner les tests sur une configuration et une base isolées de celles du serveur de développement, sans dupliquer de code. Si vous préfèrez un style plus simple pour le jour 1 (un seul fichier `app.py`), rien n'empêche de repartir de zéro sur cette base — le cahier des charges laisse le choix ouvert.

## Mise en route

```bash
# 1. Créer et activer un environnement virtuel
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux / macOS

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Copier le fichier d'environnement
copy .env.example .env        # Windows
cp .env.example .env          # Linux / macOS

# 4. Initialiser la base (crée les tables déclarées dans app/models)
python seed.py

# 5. Lancer le serveur
python run.py

# 6. Lancer les tests
pytest
```

L'environnement virtuel (`.venv/`) n'est pas versionné (voir `.gitignore`) : chaque personne de l'équipe le recrée localement à partir de `requirements.txt`. C'est `requirements.txt`, pas le dossier `.venv`, qui doit être commité.

## Où continuer

Le modèle de données à implémenter dans `app/models/` est détaillé dans `schema-bdd-academie-sorcellerie.md` à la racine du projet.

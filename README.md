# Académie de Sorcellerie — squelette de départ

Ceci est un point de départ, pas une base à compléter à l'identique : la structure des fichiers reste entre vos mains, comme le précise le cahier des charges. Ce squelette pose juste les choses qui seraient fastidieuses à remettre en place vous-mêmes en début de jour 1 : l'app factory Flask, la connexion SQLAlchemy, les modèles de données, et un premier test qui prouve que tout ça démarre.

Le README complet (installation, variables d'environnement, seed, tests) attendu en livrable du jour 4 est à écrire par vous-même au fil du projet — celui-ci ne couvre que la mise en route de ce squelette.

## Avancement

Fait : les modèles de données (`app/models/`), écrits avec la syntaxe déclarative typée de SQLAlchemy 2.0 (`Mapped[...]` / `mapped_column()`), couvrant les 13 entités du schéma complet (jours 1 à 4) — voir `schema-bdd-academie-sorcellerie.md` pour le détail de chaque table et de ses relations.

Reste à faire : peuplement de la base (`seed.py`), CRUD sur Maison/Professeur/Cours/Élève, connexion simulée (`POST /login` + header `X-User-Id`). Voir "Où continuer" plus bas.

## Structure

```
.
├── app/
│   ├── __init__.py       # create_app() : app factory, enregistre modèles et blueprints
│   ├── extensions.py     # instance unique de SQLAlchemy (db)
│   ├── models/
│   │   ├── __init__.py       # agrège les imports, nécessaire à db.create_all()
│   │   ├── mixins.py          # TimestampMixin (created_at / updated_at)
│   │   ├── enums.py           # StatutEleve, RoleUtilisateur, StatutInscription, SourceDeblocage
│   │   ├── annee_academique.py
│   │   ├── maison.py
│   │   ├── professeur.py
│   │   ├── cours.py
│   │   ├── eleve.py
│   │   ├── utilisateur.py
│   │   ├── inscription.py
│   │   ├── examen.py
│   │   ├── resultat.py
│   │   ├── competence.py
│   │   ├── maitrise.py
│   │   ├── tournoi.py
│   │   └── duel.py
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

Pourquoi une app factory plutôt qu'un fichier unique : le projet grossit vite (une dizaine de ressources sur 4 jours), et l'app factory permet de faire tourner les tests sur une configuration et une base isolées de celles du serveur de développement, sans dupliquer de code. Si votre équipe préfère un style plus simple pour le jour 1 (un seul fichier `app.py`), rien n'empêche de repartir de zéro sur cette base — le cahier des charges laisse le choix ouvert.

Pourquoi un module par entité dans `app/models/` : ça garde chaque fichier court et les diffs Git lisibles à plusieurs sur la semaine. Les imports croisés entre entités (ex. `Eleve` référence `Maison`) passent par des chaînes de caractères dans `relationship(...)` plutôt que par des imports directs, pour éviter les imports circulaires — voir le bloc `if TYPE_CHECKING:` en haut de chaque fichier.

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

# 4. Initialiser la base (crée les 13 tables déclarées dans app/models)
python seed.py

# 5. Lancer le serveur
python run.py

# 6. Lancer les tests
pytest
```

L'environnement virtuel (`.venv/`) n'est pas versionné (voir `.gitignore`) : chaque personne de l'équipe le recrée localement à partir de `requirements.txt`. C'est `requirements.txt`, pas le dossier `.venv`, qui doit être commité.

## Où continuer

Le modèle de données est en place. Les étapes suivantes du jour 1, dans un ordre raisonnable :

Compléter `seed.py` : créer au moins 4 maisons, une trentaine d'élèves répartis sur les 7 années, quelques professeurs et cours, et un utilisateur par élève/professeur plus un compte admin. Gardez à l'esprit dès maintenant que le script doit rester rejouable sans dupliquer ni casser les données (critère du jour 4) — autant prendre l'habitude tout de suite.

Écrire le CRUD sur Maison, Professeur, Cours et Élève : un blueprint par ressource dans `app/routes/`, sur le modèle de `health.py`, enregistré dans `register_blueprints()` (`app/__init__.py`).

Mettre en place `POST /login` et la lecture du header `X-User-Id` sur les endpoints qui distinguent espace élève / espace admin, avec le comportement d'erreur explicite (401/400) décrit dans le cahier des charges si le header manque.

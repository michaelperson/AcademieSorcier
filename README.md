# Académie de Sorcellerie — squelette de départ

Ceci est un point de départ, pas une base à compléter à l'identique : la structure des fichiers reste entre vos mains, comme le précise le cahier des charges. Ce squelette pose les choses qui seraient fastidieuses à remettre en place vous-mêmes en début de semaine : l'app factory Flask, la connexion SQLAlchemy, les modèles de données, le seed, le CRUD de base, la connexion simulée et la documentation API interactive.

Le README complet (installation, variables d'environnement, seed, tests, exemples curl) attendu en livrable du jour 4 est à écrire par vous-même au fil du projet — celui-ci ne couvre que la mise en route de ce squelette.

## Avancement

Jour 1 fait : modèles de données (`app/models/`, syntaxe déclarative typée SQLAlchemy 2.0), seed rejouable et idempotent (`seed.py`), CRUD complet sur Maison/Professeur/Cours/Élève (`app/routes/`), connexion simulée (`POST /login`, header `X-User-Id` via `app/auth.py`, démontré par `GET /whoami`).

En plus du jour 1 : documentation OpenAPI (`app/openapi_spec.py`) servie à `/openapi.json` et affichée avec Scalar sur `/docs`. Écrite à la main plutôt que générée : à ce stade il n'y a pas encore de bibliothèque de validation de schéma (marshmallow/pydantic arrivent jour 4) à introspecter. Pensez à la tenir à jour au fil des jours suivants, au même titre que le README.

Reste à faire : jour 2 — inscriptions (association enrichie Élève ↔ Cours), examens, résultats, clôture d'examen, chasse au N+1. Voir "Où continuer" plus bas.

## Structure

```
.
├── app/
│   ├── __init__.py       # create_app() : app factory, enregistre modèles et blueprints
│   ├── extensions.py     # instance unique de SQLAlchemy (db)
│   ├── auth.py           # lecture X-User-Id, décorateurs connexion_requise / role_requis
│   ├── openapi_spec.py   # spec OpenAPI écrite à la main (dict Python)
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
│       ├── health.py       # GET /health
│       ├── auth.py         # POST /login, GET /whoami
│       ├── docs.py         # GET /openapi.json, GET /docs (Scalar)
│       ├── maisons.py      # CRUD Maison
│       ├── professeurs.py  # CRUD Professeur
│       ├── cours.py        # CRUD Cours
│       └── eleves.py       # CRUD Élève
├── tests/
│   ├── conftest.py       # fixtures app / client / maison / professeur / eleve / utilisateurs
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_maisons.py
│   ├── test_professeurs.py
│   ├── test_cours.py
│   └── test_eleves.py
├── config.py             # Config (dev) / TestingConfig
├── run.py                # lance le serveur de développement
├── seed.py                # peuple la base (4 maisons, 30 élèves, 5 professeurs, 5 cours, comptes)
├── requirements.txt
└── .env.example
```

Pourquoi une app factory plutôt qu'un fichier unique : le projet grossit vite (une dizaine de ressources sur 4 jours), et l'app factory permet de faire tourner les tests sur une configuration et une base isolées de celles du serveur de développement, sans dupliquer de code. Si votre équipe préfère un style plus simple (un seul fichier `app.py`), rien n'empêche de repartir de zéro sur cette base — le cahier des charges laisse le choix ouvert.

Pourquoi un module par entité dans `app/models/` : ça garde chaque fichier court et les diffs Git lisibles à plusieurs sur la semaine. Les imports croisés entre entités passent par des chaînes de caractères dans `relationship(...)` plutôt que par des imports directs, pour éviter les imports circulaires — voir le bloc `if TYPE_CHECKING:` en haut de chaque fichier.

Pourquoi le CRUD n'est pas protégé par rôle : le critère de fin de jour 1 du cahier des charges veut que chaque ressource soit "créée, lue, modifiée et supprimée" librement pour vérifier que le CRUD fonctionne. Le mécanisme de rôle (`app/auth.py`, `role_requis(...)`) est prêt et testé (`GET /whoami`) ; c'est à partir du jour 2 que le cahier des charges introduit des endpoints qui doivent réellement distinguer espace élève et espace admin ("mes cours", "mes notes"...). Si votre équipe préfère verrouiller le CRUD dès maintenant, il suffit d'ajouter `@role_requis(RoleUtilisateur.ADMIN)` au-dessus des vues d'écriture.

Pourquoi Scalar plutôt que Swagger UI ou flask-smorest : Scalar se résume à une page HTML statique (`app/routes/docs.py`) qui charge un script depuis un CDN et lit `/openapi.json` — aucune dépendance Python à ajouter à `requirements.txt`. C'est un choix d'outil d'affichage, pas d'architecture : n'importe quelle autre interface compatible OpenAPI (Swagger UI, Redoc...) fonctionnerait avec la même spec.

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

# 4. Peupler la base (4 maisons, 30 élèves, 5 professeurs, 5 cours, un compte par personne + admin)
python seed.py

# 5. Lancer le serveur
python run.py

# 6. Lancer les tests
pytest
```

L'environnement virtuel (`.venv/`) n'est pas versionné (voir `.gitignore`) : chaque personne de l'équipe le recrée localement à partir de `requirements.txt`.

### Essayer rapidement

```bash
curl http://127.0.0.1:5000/health

curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@academie-sorcellerie.fr", "mot_de_passe": "admin123"}'

# Avec l'id renvoyé par /login :
curl http://127.0.0.1:5000/whoami -H "X-User-Id: 36"

curl http://127.0.0.1:5000/maisons
```

Tous les comptes créés par `seed.py` utilisent le mot de passe `motdepasse123` (élèves et professeurs) ou `admin123` (le compte admin), sur le modèle `prenom.nom@academie-sorcellerie.fr`.

Ouvrez `http://127.0.0.1:5000/docs` dans un navigateur pour la documentation interactive (Scalar) : tous les endpoints listés ci-dessus y sont décrits avec leurs schémas de requête/réponse.

## Où continuer

Le jour 1 est complet au sens du cahier des charges, plus une documentation OpenAPI/Scalar en avance sur le planning. La suite, c'est le jour 2 :

Inscription : association enrichie Élève ↔ Cours (date d'inscription, statut), avec refus propre si le cours a atteint sa capacité maximale.

Examen et Résultat : rattacher un examen à un cours, saisir les résultats en masse (un payload avec la liste des notes, pas un appel par élève), puis l'endpoint métier de clôture d'examen qui met à jour le statut des inscriptions et calcule la moyenne du cours.

Chasse au N+1 : activer `SQLALCHEMY_ECHO`, compter les requêtes sur un endpoint de listing qui accède à une relation en boucle (ex. `eleve.maison.nom` pour chaque élève d'un cours), corriger avec `joinedload()`/`selectinload()` rendu optionnel par un paramètre de requête, et documenter l'avant/après.

N'oubliez pas d'ajouter les nouveaux endpoints du jour 2 à `app/openapi_spec.py` au fur et à mesure — une doc qui prend du retard sur le code perd vite sa valeur.

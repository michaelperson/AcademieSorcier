# Académie de Sorcellerie — squelette de départ

Ceci est un point de départ, pas une base à compléter à l'identique : la structure des fichiers reste entre vos mains, comme le précise le cahier des charges. Ce squelette pose les choses qui seraient fastidieuses à remettre en place vous-mêmes en début de semaine : l'app factory Flask, la connexion SQLAlchemy, les modèles de données, le seed, le CRUD de base, la connexion simulée et la documentation API interactive.

Le README complet (installation, variables d'environnement, seed, tests, exemples curl) attendu en livrable du jour 4 est à écrire par vous-même au fil du projet — celui-ci ne couvre que la mise en route de ce squelette.

## Avancement

Jour 1 fait : modèles de données (`app/models/`, syntaxe déclarative typée SQLAlchemy 2.0), seed rejouable et idempotent (`seed.py`), CRUD complet sur Maison/Professeur/Cours/Élève (`app/routes/`), connexion simulée (`POST /login`, header `X-User-Id` via `app/auth.py`, démontré par `GET /whoami`), documentation OpenAPI (`app/openapi_spec.py`) servie à `/openapi.json` et affichée avec Scalar sur `/docs`.

Jour 2 fait :

Inscription (`app/routes/inscriptions.py`) : `POST /cours/<id>/inscriptions` inscrit un élève avec refus propre (400) si le cours a atteint sa `capacite_max` ou si l'élève est déjà inscrit.

Examen et Résultat (`app/routes/examens.py`, `app/routes/resultats.py`) : CRUD examen rattaché à un cours, saisie des résultats en masse (`POST /examens/<id>/resultats`, un payload avec la liste des notes, validation atomique — soit tout est enregistré, soit rien), listing filtrable (`GET /resultats?cours_id=...&examen_id=...`) et moyenne de cours (`GET /cours/<id>/moyenne`).

Clôture d'examen et clôture de cours — deux endpoints distincts, sur deux statuts distincts (spec précisée le 2026-07-08, après une première version qui les confondait) :

- `POST /examens/<id>/cloture` décide, pour chaque élève ayant un résultat à CET examen, s'il l'a réussi ou échoué. Écrit sur `Resultat.statut`, refuse (400) tant qu'un élève du cours n'a pas encore de résultat.
- `POST /cours/<id>/cloture` calcule la moyenne d'un élève sur TOUS les examens du cours et en tire la mise à jour de `Inscription.statut`. Deux modes : sans `?eleve_id=`, un rapport en lecture seule sur toute la classe ; avec, la décision (et l'écriture en base) pour cet élève-là seulement.

Les deux notions ne doivent pas être confondues : un élève peut échouer un examen isolé et rester "en_cours" dans le cours si sa moyenne générale suffit. Le détail des choix pris là où le cahier des charges reste ouvert (le seuil de réussite retenu au niveau du cours, en l'absence d'un tel champ en base) est documenté dans les docstrings de `app/routes/examens.py`.

Espace élève (`app/routes/espace_eleve.py`) : `GET /moi/cours`, `GET /moi/notes`, `GET /moi/dossier`, tous scopés sur l'élève résolu via `X-User-Id` et protégés par `role_requis(RoleUtilisateur.ELEVE)`.

Chasse au N+1 : mesure réelle (pas théorique) des requêtes SQL sur `GET /cours/<id>/eleves`, correctif par `joinedload()` rendu optionnel via `?eager=true`, avant/après documenté dans `PERFORMANCE.md`.

Gestion d'erreurs centralisée et logging (`app/error_handlers.py`, `app/logging_config.py`) : ajoutés hors cahier des charges, à la suite d'un bug réel rencontré en cours de route (une base non initialisée renvoyait une page HTML de débogage au lieu d'une erreur JSON). Détail plus bas dans cette section.

72 tests passent (`pytest`), dont les tests métier attendus par le cahier des charges : refus d'inscription sur cours complet, décision réussi/échec à la clôture d'un examen, et mise à jour de l'inscription à la clôture d'un cours.

Reste à faire : jour 3 — compétences, maîtrise, tournoi, duel. Voir "Où continuer" plus bas.

### Gestion d'erreurs et logging

Deux fichiers, deux responsabilités séparées :

`app/error_handlers.py` centralise la conversion des exceptions en réponses JSON, avec `app.errorhandler(...)` — l'équivalent Flask d'un middleware d'exception (Flask n'a pas de chaîne de middlewares au sens Express ou Django). Trois niveaux, du plus spécifique au plus général : les `HTTPException` de Flask/Werkzeug (route inconnue, méthode non supportée — auparavant renvoyées en HTML, incohérent avec le reste de l'API), les `SQLAlchemyError` (avec `db.session.rollback()`, indispensable pour ne pas laisser la session dans un état invalide pour la requête suivante), et enfin `Exception` en filet de sécurité pour tout le reste. Ce mécanisme ne remplace pas les validations déjà faites route par route (champ manquant, cours complet...) : il couvre ce qu'aucune route ne peut anticiper.

`app/logging_config.py` configure le logger applicatif (niveau piloté par `LOG_LEVEL`, sortie console toujours, fichier tournant optionnel dans `logs/` via `LOG_TO_FILE=True`) et un journal d'accès séparé (une ligne par requête : méthode, chemin, code retour, durée), via les hooks `before_request`/`after_request`.

Pourquoi ajouter ça maintenant, hors planning : en testant l'API sans avoir lancé `seed.py`, une requête sur un endpoint de listing plantait avec une trace SQLAlchemy brute et la page de débogage interactive de Werkzeug (avec son PIN de déverrouillage) au lieu d'une erreur exploitable. Symptomatique d'un problème plus général : sans gestion centralisée, chaque route qui pourrait un jour lever une exception imprévue devrait la gérer elle-même, ou la laisser fuiter telle quelle. Le correctif ponctuel (lancer le seed) ne change rien à ce problème de fond.

## Structure

```
.
├── app/
│   ├── __init__.py       # create_app() : app factory, enregistre modèles, logging, erreurs, blueprints
│   ├── extensions.py     # instance unique de SQLAlchemy (db)
│   ├── auth.py           # lecture X-User-Id, décorateurs connexion_requise / role_requis
│   ├── error_handlers.py # gestion centralisée des exceptions (HTTPException, SQLAlchemyError, Exception)
│   ├── logging_config.py # logger applicatif + journal d'accès (before_request/after_request)
│   ├── openapi_spec.py   # spec OpenAPI écrite à la main (dict Python)
│   ├── models/
│   │   ├── __init__.py       # agrège les imports, nécessaire à db.create_all()
│   │   ├── mixins.py          # TimestampMixin (created_at / updated_at)
│   │   ├── enums.py           # StatutEleve, RoleUtilisateur, StatutInscription, StatutResultat, SourceDeblocage
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
│       ├── health.py          # GET /health
│       ├── auth.py            # POST /login, GET /whoami
│       ├── docs.py            # GET /openapi.json, GET /docs (Scalar)
│       ├── maisons.py         # CRUD Maison
│       ├── professeurs.py     # CRUD Professeur
│       ├── cours.py           # CRUD Cours
│       ├── eleves.py          # CRUD Élève
│       ├── inscriptions.py    # POST /cours/<id>/inscriptions, GET /cours/<id>/eleves (N+1)
│       ├── examens.py         # CRUD Examen, résultats en masse, clôture d'examen, clôture de cours
│       ├── resultats.py       # GET /resultats, GET /cours/<id>/moyenne
│       └── espace_eleve.py    # GET /moi/cours, /moi/notes, /moi/dossier
├── tests/
│   ├── conftest.py         # fixtures app / client / maison / professeur / cours / eleve(s) / utilisateurs
│   ├── test_health.py
│   ├── test_auth.py
│   ├── test_maisons.py
│   ├── test_professeurs.py
│   ├── test_cours.py
│   ├── test_eleves.py
│   ├── test_inscriptions.py
│   ├── test_examens.py
│   ├── test_espace_eleve.py
│   ├── test_resultats.py
│   └── test_error_handlers.py
├── config.py             # Config (dev) / TestingConfig, dont LOG_LEVEL / LOG_TO_FILE
├── run.py                # lance le serveur de développement
├── seed.py               # peuple la base (4 maisons, 30 élèves, 5 professeurs, 5 cours, comptes)
├── PERFORMANCE.md        # chasse au N+1 : méthode de mesure, résultats, correctif
├── logs/                 # créé si LOG_TO_FILE=True (ignoré par git)
├── requirements.txt
└── .env.example
```

Pourquoi une app factory plutôt qu'un fichier unique : le projet grossit vite (une dizaine de ressources sur 4 jours), et l'app factory permet de faire tourner les tests sur une configuration et une base isolées de celles du serveur de développement, sans dupliquer de code. Si votre équipe préfère un style plus simple (un seul fichier `app.py`), rien n'empêche de repartir de zéro sur cette base — le cahier des charges laisse le choix ouvert.

Pourquoi un module par entité dans `app/models/` : ça garde chaque fichier court et les diffs Git lisibles à plusieurs sur la semaine. Les imports croisés entre entités passent par des chaînes de caractères dans `relationship(...)` plutôt que par des imports directs, pour éviter les imports circulaires — voir le bloc `if TYPE_CHECKING:` en haut de chaque fichier.

Pourquoi le CRUD Maison/Professeur/Cours/Élève n'est pas protégé par rôle : le critère de fin de jour 1 du cahier des charges veut que chaque ressource soit "créée, lue, modifiée et supprimée" librement pour vérifier que le CRUD fonctionne. Le mécanisme de rôle (`app/auth.py`, `role_requis(...)`) est prêt et testé (`GET /whoami`) ; le jour 2 l'utilise pour de bon sur l'espace élève (`/moi/...`), qui doit rester strictement scopé à l'élève qui consulte. Si votre équipe préfère verrouiller le CRUD dès maintenant, il suffit d'ajouter `@role_requis(RoleUtilisateur.ADMIN)` au-dessus des vues d'écriture.

Pourquoi Scalar plutôt que Swagger UI ou flask-smorest : Scalar se résume à une page HTML statique (`app/routes/docs.py`) qui charge un script depuis un CDN et lit `/openapi.json` — aucune dépendance Python à ajouter à `requirements.txt`. C'est un choix d'outil d'affichage, pas d'architecture : n'importe quelle autre interface compatible OpenAPI (Swagger UI, Redoc...) fonctionnerait avec la même spec.

Pourquoi deux statuts séparés, `Resultat.statut` et `Inscription.statut` : ce sont deux questions différentes. "Cet élève a-t-il réussi CET examen ?" se répond au niveau du résultat, avec le seuil de CET examen. "Cet élève a-t-il réussi LE COURS ?" se répond au niveau de l'inscription, avec la moyenne de TOUS ses examens dans ce cours. Les confondre (comme le faisait une première version de cet endpoint) revient à laisser un seul examen décider du sort de tout le cours, ce que le cahier des charges ne demande pas. D'où deux endpoints (`/examens/<id>/cloture` et `/cours/<id>/cloture`) plutôt qu'un seul qui ferait les deux à moitié.

Pourquoi le mode sans `eleve_id` de `/cours/<id>/cloture` ne modifie rien : c'est un rapport, pas une clôture en masse. Clôturer tous les élèves d'un coup sans validation professeur par professeur serait un raccourci que le cahier des charges ne demande pas explicitement (il ne parle que d'un `eleve_id` facultatif, pas d'un mode "tout clôturer") ; le mode rapport permet de vérifier les moyennes avant de déclencher les mises à jour une par une.

Pourquoi le chargement anticipé (`joinedload`) est optionnel plutôt qu'activé par défaut : voir `PERFORMANCE.md`. En résumé, le coût existe (plus de colonnes ramenées par ligne) et n'a de sens que sur un accès en boucle — l'imposer partout serait une optimisation prématurée.

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

Important sur `DATABASE_URL` dans `.env` : laissez la ligne commentée par défaut. `config.py` utilise alors un chemin absolu (`<racine du projet>/academie.db`). Si vous la décommentez avec un chemin relatif comme `sqlite:///academie.db`, Flask-SQLAlchemy le résout par rapport au dossier `instance/` de Flask, pas à la racine du projet — vous auriez alors deux fichiers `.db` différents selon que la variable est définie ou non, avec `seed.py` qui peuple l'un et le serveur qui lit l'autre (symptôme : `OperationalError: no such table`, alors que le seed s'est pourtant bien déroulé).

### Essayer rapidement

```bash
curl http://127.0.0.1:5000/health

curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@academie-sorcellerie.fr", "mot_de_passe": "admin123"}'

# Avec l'id renvoyé par /login :
curl http://127.0.0.1:5000/whoami -H "X-User-Id: 36"

curl http://127.0.0.1:5000/maisons

# Inscrire un élève à un cours
curl -X POST http://127.0.0.1:5000/cours/1/inscriptions \
  -H "Content-Type: application/json" -d '{"eleve_id": 1}'

# Chasse au N+1 : comparer le nombre de requêtes SQL dans les logs
# (SQLALCHEMY_ECHO=True dans .env) entre les deux appels suivants
curl http://127.0.0.1:5000/cours/1/eleves
curl http://127.0.0.1:5000/cours/1/eleves?eager=true

# Clôturer un examen (statut réussi/échec par élève, sur cet examen)
curl -X POST http://127.0.0.1:5000/examens/1/cloture

# Clôture de cours : rapport sur toute la classe, puis décision pour un élève
curl -X POST http://127.0.0.1:5000/cours/1/cloture
curl -X POST "http://127.0.0.1:5000/cours/1/cloture?eleve_id=1"

# Gestion d'erreurs centralisée : réponse JSON, pas une page HTML
curl http://127.0.0.1:5000/route-qui-nexiste-pas
curl -X DELETE http://127.0.0.1:5000/health
```

Tous les comptes créés par `seed.py` utilisent le mot de passe `motdepasse123` (élèves et professeurs) ou `admin123` (le compte admin), sur le modèle `prenom.nom@academie-sorcellerie.fr`.

Ouvrez `http://127.0.0.1:5000/docs` dans un navigateur pour la documentation interactive (Scalar) : tous les endpoints listés ci-dessus y sont décrits avec leurs schémas de requête/réponse.

## Où continuer

Le jour 2 est complet au sens du cahier des charges. La suite, c'est le jour 3 :

Compétence et Maîtrise : modéliser les compétences qu'un élève peut acquérir dans une matière, avec un niveau de maîtrise qui progresse (probablement via les résultats d'examen ou une validation manuelle — à trancher en équipe, le cahier des charges laisse la mécanique ouverte).

Tournoi et Duel : organiser des duels entre élèves dans le cadre d'un tournoi, avec un vainqueur et un impact sur la réputation de la maison (`Maison.reputation`, déjà présent en base mais jamais modifié jusqu'ici — jour 3 est l'endroit où ce champ prend enfin un sens).

Comme pour le jour 2 : ajoutez les nouveaux endpoints à `app/openapi_spec.py` au fur et à mesure, et si un nouvel endpoint de listing boucle sur une relation, vérifiez d'abord s'il y a un N+1 avant de l'écrire en dur — le réflexe posé dans `PERFORMANCE.md` vaut pour la suite du projet, pas seulement pour `/cours/<id>/eleves`.

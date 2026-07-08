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

67 tests passent (`pytest`), dont les tests métier attendus par le cahier des charges : refus d'inscription sur cours complet, décision réussi/échec à la clôture d'un examen, et mise à jour de l'inscription à la clôture d'un cours.

Reste à faire : jour 3 — compétences, maîtrise, tournoi, duel. Voir "Où continuer" plus bas.

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
│   └── test_resultats.py
├── config.py             # Config (dev) / TestingConfig
├── run.py                # lance le serveur de développement
├── seed.py               # peuple la base (4 maisons, 30 élèves, 5 professeurs, 5 cours, comptes)
├── PERFORMANCE.md        # chasse au N+1 : méthode de mesure, résultats, correctif
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
```

Tous les comptes créés par `seed.py` utilisent le mot de passe `motdepasse123` (élèves et professeurs) ou `admin123` (le compte admin), sur le modèle `prenom.nom@academie-sorcellerie.fr`.

Ouvrez `http://127.0.0.1:5000/docs` dans un navigateur pour la documentation interactive (Scalar) : tous les endpoints listés ci-dessus y sont décrits avec leurs schémas de requête/réponse.

## Où continuer

Le jour 2 est complet au sens du cahier des charges. La suite, c'est le jour 3 :

Compétence et Maîtrise : modéliser les compétences qu'un élève peut acquérir dans une matière, avec un niveau de maîtrise qui progresse (probablement via les résultats d'examen ou une validation manuelle — à trancher en équipe, le cahier des charges laisse la mécanique ouverte).

Tournoi et Duel : organiser des duels entre élèves dans le cadre d'un tournoi, avec un vainqueur et un impact sur la réputation de la maison (`Maison.reputation`, déjà présent en base mais jamais modifié jusqu'ici — jour 3 est l'endroit où ce champ prend enfin un sens).

Comme pour le jour 2 : ajoutez les nouveaux endpoints à `app/openapi_spec.py` au fur et à mesure, et si un nouvel endpoint de listing boucle sur une relation, vérifiez d'abord s'il y a un N+1 avant de l'écrire en dur — le réflexe posé dans `PERFORMANCE.md` vaut pour la suite du projet, pas seulement pour `/cours/<id>/eleves`.

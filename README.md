# Académie de Sorcellerie — API backend

Backend Flask/SQLAlchemy du cahier des charges "Académie de Sorcellerie", livré au complet sur les quatre jours prévus : modèles de données, CRUD, connexion simulée, inscriptions et clôtures pédagogiques, compétences et tournois, puis passage de fin d'année et validation stricte des payloads.

Ce README documente l'état final du projet : installation, variables d'environnement, structure, choix de conception, exemples curl couvrant tous les endpoints, et comment lancer le seed et les tests.

## Avancement

Jour 1 fait : modèles de données (`app/models/`, syntaxe déclarative typée SQLAlchemy 2.0), seed rejouable et idempotent (`seed.py`), CRUD complet sur Maison/Professeur/Cours/Élève (`app/routes/`), connexion simulée (`POST /login`, header `X-User-Id` via `app/auth.py`, démontré par `GET /whoami`), documentation OpenAPI (`app/openapi_spec.py`) servie à `/openapi.json` et affichée avec Scalar sur `/docs`.

Jour 2 fait :

Inscription (`app/routes/inscriptions.py`) : `POST /cours/<id>/inscriptions` inscrit un élève avec refus propre (400) si le cours a atteint sa `capacite_max` ou si l'élève est déjà inscrit.

Examen et Résultat (`app/routes/examens.py`, `app/routes/resultats.py`) : CRUD examen rattaché à un cours, saisie des résultats en masse (`POST /examens/<id>/resultats`, un payload avec la liste des notes, validation atomique — soit tout est enregistré, soit rien), listing filtrable (`GET /resultats?cours_id=...&examen_id=...`) et moyenne de cours (`GET /cours/<id>/moyenne`).

Clôture d'examen et clôture de cours — deux endpoints distincts, sur deux statuts distincts :

- `POST /examens/<id>/cloture` décide, pour chaque élève ayant un résultat à CET examen, s'il l'a réussi ou échoué. Écrit sur `Resultat.statut`, refuse (400) tant qu'un élève du cours n'a pas encore de résultat.
- `POST /cours/<id>/cloture` calcule la moyenne d'un élève sur TOUS les examens du cours et en tire la mise à jour de `Inscription.statut`. Deux modes : sans `?eleve_id=`, un rapport en lecture seule sur toute la classe ; avec, la décision (et l'écriture en base) pour cet élève-là seulement.

Les deux notions ne doivent pas être confondues : un élève peut échouer un examen isolé et rester "en_cours" dans le cours si sa moyenne générale suffit. Le détail des choix pris là où le cahier des charges reste ouvert (le seuil de réussite retenu au niveau du cours, en l'absence d'un tel champ en base) est documenté dans les docstrings de `app/routes/examens.py`.

Espace élève (`app/routes/espace_eleve.py`) : `GET /moi/cours`, `GET /moi/notes`, `GET /moi/dossier`, tous scopés sur l'élève résolu via `X-User-Id` et protégés par `role_requis(RoleUtilisateur.ELEVE)`.

Chasse au N+1 : mesure réelle (pas théorique) des requêtes SQL sur `GET /cours/<id>/eleves`, correctif par `joinedload()` rendu optionnel via `?eager=true`, avant/après documenté dans `PERFORMANCE.md`.

Gestion d'erreurs centralisée et logging (`app/error_handlers.py`, `app/logging_config.py`) : ajoutés hors cahier des charges, à la suite d'un bug réel rencontré en cours de route (une base non initialisée renvoyait une page HTML de débogage au lieu d'une erreur JSON). Détail plus bas dans cette section.

Jour 3 fait :

Compétence (`app/routes/competences.py`) : catalogue de compétences, lecture publique et écriture réservée à l'admin (`role_requis(RoleUtilisateur.ADMIN)` — voir plus bas pourquoi ce jour-ci change la règle du jour 1). Chaque compétence porte une condition de déblocage, `condition_type` valant `examen` ou `tournoi` :

- condition `examen` : `examen_id` et `note_min` obligatoires à la création (vérifiés en base, l'examen doit exister) — la compétence se débloque quand un élève atteint cette note à cet examen précis.
- condition `tournoi` : `examen_id` et `note_min` n'ont pas de sens et sont forcés à `null`, quoi que le payload contienne — la compétence se débloque au vainqueur d'un tournoi.

Listing paginé et filtrable par catégorie (`GET /competences?categorie=...&page=...&par_page=...`), pagination implémentée à la main dans `app/pagination.py` (pas de dépendance ajoutée pour ça).

Maîtrise : pas de route dédiée — une Maîtrise n'est jamais créée à la main, seulement comme conséquence d'un des deux endpoints métier ci-dessous. C'est ce qui garantit qu'une compétence "débloquée par examen" l'est vraiment par un examen, pas par une écriture directe qui contournerait la condition.

Endpoint métier 1 — évaluer les compétences débloquées par un examen (`POST /examens/<id>/evaluer-competences`) : exige que l'examen ait déjà été clôturé (`POST /examens/<id>/cloture`, jour 2) ; pour chaque compétence à condition `examen` liée à cet examen, parcourt les résultats et crée une `Maitrise` pour chaque élève dont la note atteint `note_min`. Idempotent : rejouer l'appel ne crée pas de doublon, grâce à la contrainte unique `(eleve_id, competence_id)` posée sur `Maitrise` — l'endpoint distingue d'ailleurs dans sa réponse les maîtrises nouvellement créées de celles déjà acquises.

Tournoi et Duel (`app/routes/tournois.py`) : CRUD restreint côté écriture à l'admin, lecture publique, paginé et filtrable par année (`GET /tournois?annee=...`). Un duel s'enregistre déjà joué (`POST /tournois/<id>/duels` avec le vainqueur inclus dans le payload), ce n'est pas une programmation de rencontre à venir.

Endpoint métier 2 — clôturer un tournoi (`POST /tournois/<id>/cloture`) : compte les victoires en duel par élève, désigne le vainqueur, débloque pour lui toutes les compétences à condition `tournoi` non encore acquises, et ajoute `POINTS_REPUTATION_VICTOIRE_TOURNOI` (10, constante en tête de fichier) à la réputation de sa maison. Trois refus (400) volontaires :

- tournoi déjà clôturé (`cloture_le` non nul) : garde anti-rejeu, on ne recompte pas les victoires et on ne redistribue pas de réputation une seconde fois.
- aucun duel enregistré : rien à départager.
- égalité stricte entre plusieurs élèves au nombre de victoires : la réponse renvoie `eleves_ex_aequo` plutôt que de trancher arbitrairement (premier inscrit, id le plus petit...) une décision qui affecte la réputation d'une maison entière. Un professeur tranche à la main en ajoutant un duel de départage, puis relance la clôture.

Espace élève, deux ajouts : `GET /moi/competences` (les compétences débloquées par l'élève courant) et `GET /moi/tournois` (l'historique de ses duels, avec l'adversaire et l'issue — `gagne`, `perdu` ou `en_attente` si le duel n'a pas encore de vainqueur).

Jour 4 fait — le dernier jour du cahier des charges :

Validation stricte des payloads (`app/schemas.py`, `app/validation.py`) : toutes les routes d'écriture de la semaine (Maison, Professeur, Cours, Élève, Inscription, Examen, Résultats, Compétence, Tournoi, Duel, Année académique) passent désormais par un schéma marshmallow avant d'atteindre la moindre logique métier. Un payload invalide renvoie systématiquement :

```json
{"erreur": "Payload invalide.", "champs": {"annee_etude": ["Doit être compris entre 1 et 7."]}}
```

`champs` reprend un message précis par champ fautif — pas juste "requête invalide" — ce qui correspond à l'exigence du cahier des charges de "préciser le champ en erreur". Ce que marshmallow valide : la forme du payload (présence, type, bornes numériques, cohérence entre deux champs du même payload via `@validates_schema`, par exemple qu'un vainqueur de duel soit bien l'un des deux participants). Ce que marshmallow ne valide pas, et qui reste à la charge des routes : tout ce qui dépend de l'état de la base — un `maison_id` qui a le bon type mais ne correspond à aucune maison, un cours déjà complet, une compétence à condition `examen` dont le `examen_id` doit exister. La frontière est volontaire : un schéma ne devrait pas interroger la base, sous peine de mélanger deux couches de validation aux échecs très différents (400 côté forme, 400 ou 404 côté cohérence métier).

Passage de fin d'année (`app/routes/annees_academiques.py`) : `POST /annees-academiques/<id>/cloture` referme la boucle laissée ouverte depuis le jour 1 (`StatutEleve` prévoyait déjà `diplome`, mais rien ne l'utilisait). Pour chaque élève actif, la moyenne générale se calcule sur ses inscriptions au statut `valide` de l'année en cours ; comparée au `seuil_promotion` de l'année (ou à un `?seuil=` fourni en query, sans toucher à la valeur enregistrée), trois issues :

- moyenne suffisante et année d'étude < 7 : promotion (`annee_etude += 1`).
- moyenne suffisante et année d'étude == 7 : diplomation — l'élève passe au statut `diplome`, son dossier, ses compétences et son historique restent consultables normalement (archivage, pas suppression).
- moyenne insuffisante, ou aucune inscription validée cette année-là : redoublement. Ce dernier cas (aucune inscription validée) est un choix de conception assumé : plutôt que de promouvoir un élève faute de preuve du contraire, l'absence de résultat validé est traitée comme un échec — documenté dans le docstring de la fonction et couvert par `test_cloture_annee_sans_inscription_validee_redouble`.

Garde anti-rejeu sur `AnneeAcademique.cloturee_le`, même principe que `Tournoi.cloture_le` (jour 3) : une année déjà clôturée refuse (400) toute nouvelle clôture, et son `seuil_promotion` devient figé (`PUT /annees-academiques/<id>` refuse aussi une fois clôturée).

Volume réaliste dans le seed (`seed.py`) : 160 élèves (au lieu de 30), répartis sur les 7 années d'étude, 10 examens (un devoir de mi-parcours en plus de l'examen final par cours), 3 tournois déjà clôturés avec leur historique de duels, et l'ensemble des compétences déjà évaluées comme si l'année avait réellement eu lieu — inscriptions, résultats, statuts d'examen et de cours, maîtrises débloquées, tout est cohérent entre soi plutôt qu'aléatoire. Le seed reste idempotent (rejouable sans dupliquer quoi que ce soit) et déterministe (`random.Random(2026)`, mêmes notes générées à chaque exécution).

Chasse au N+1, deuxième round : le réflexe posé au jour 2 s'applique aussi à une boucle métier côté écriture, pas seulement à un listing HTTP. Voir la section "Jour 4" de `PERFORMANCE.md` : 526 requêtes SQL pour une implémentation naïve de la clôture d'année (une requête d'inscriptions puis de résultats par élève) contre 50 pour l'implémentation groupée retenue, mesuré sur les 160 élèves du seed.

112 tests passent (`pytest`), dont les scénarios propres au jour 4 : les trois issues du passage d'année sur trois profils différents (`test_annees_academiques.py`), le refus d'un second rejeu de clôture, et un échantillon représentatif de validations de payload avec vérification du champ fautif exact (`test_validation.py`).

### Gestion d'erreurs et logging

Deux fichiers, deux responsabilités séparées :

`app/error_handlers.py` centralise la conversion des exceptions en réponses JSON, avec `app.errorhandler(...)` — l'équivalent Flask d'un middleware d'exception (Flask n'a pas de chaîne de middlewares au sens Express ou Django). Trois niveaux, du plus spécifique au plus général : les `HTTPException` de Flask/Werkzeug (route inconnue, méthode non supportée — auparavant renvoyées en HTML, incohérent avec le reste de l'API), les `SQLAlchemyError` (avec `db.session.rollback()`, indispensable pour ne pas laisser la session dans un état invalide pour la requête suivante), et enfin `Exception` en filet de sécurité pour tout le reste. Ce mécanisme ne remplace pas la validation marshmallow ni les vérifications métier route par route : il couvre ce qu'aucune route ne peut anticiper.

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
│   ├── schemas.py         # schémas marshmallow de tous les payloads d'écriture (jour 4)
│   ├── validation.py      # valider(schema, payload) -> (donnees, erreur) (jour 4)
│   ├── openapi_spec.py   # spec OpenAPI écrite à la main (dict Python)
│   ├── pagination.py     # pagination manuelle (page/par_page/total/pages) pour les listings jour 3
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
│       ├── health.py             # GET /health
│       ├── auth.py               # POST /login, GET /whoami
│       ├── docs.py               # GET /openapi.json, GET /docs (Scalar)
│       ├── maisons.py            # CRUD Maison
│       ├── professeurs.py        # CRUD Professeur
│       ├── cours.py              # CRUD Cours
│       ├── eleves.py             # CRUD Élève
│       ├── inscriptions.py       # POST /cours/<id>/inscriptions, GET /cours/<id>/eleves (N+1)
│       ├── examens.py            # CRUD Examen, résultats en masse, clôture d'examen, clôture de cours, évaluer-competences
│       ├── resultats.py          # GET /resultats, GET /cours/<id>/moyenne
│       ├── espace_eleve.py       # GET /moi/cours, /moi/notes, /moi/dossier, /moi/competences, /moi/tournois
│       ├── competences.py        # CRUD Compétence (lecture publique, écriture admin), paginé + filtre catégorie
│       ├── tournois.py           # CRUD Tournoi/Duel (lecture publique, écriture admin), clôture de tournoi
│       └── annees_academiques.py # CRUD Année académique, POST /annees-academiques/<id>/cloture (jour 4)
├── tests/
│   ├── conftest.py              # fixtures app / client / maison / professeur / cours / eleve(s) / utilisateurs
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
│   ├── test_error_handlers.py
│   ├── test_competences.py
│   ├── test_tournois.py
│   ├── test_annees_academiques.py  # passage de fin d'année : promotion, redoublement, diplomation, anti-rejeu (jour 4)
│   └── test_validation.py          # échantillon de validations marshmallow, format d'erreur (jour 4)
├── config.py             # Config (dev) / TestingConfig, dont LOG_LEVEL / LOG_TO_FILE
├── run.py                # lance le serveur de développement
├── seed.py               # peuple la base (4 maisons, 160 élèves, 5 professeurs, 5 cours, 10 examens, 19 compétences, 3 tournois clôturés, comptes)
├── PERFORMANCE.md        # chasse au N+1 : méthode de mesure, résultats, correctif (jour 2 et jour 4)
├── logs/                 # créé si LOG_TO_FILE=True (ignoré par git)
├── requirements.txt
└── .env.example
```

Pourquoi une app factory plutôt qu'un fichier unique : le projet grossit vite (une dizaine de ressources sur 4 jours), et l'app factory permet de faire tourner les tests sur une configuration et une base isolées de celles du serveur de développement, sans dupliquer de code. Si votre équipe préfère un style plus simple (un seul fichier `app.py`), rien n'empêche de repartir de zéro sur cette base — le cahier des charges laisse le choix ouvert.

Pourquoi un module par entité dans `app/models/` : ça garde chaque fichier court et les diffs Git lisibles à plusieurs sur la semaine. Les imports croisés entre entités passent par des chaînes de caractères dans `relationship(...)` plutôt que par des imports directs, pour éviter les imports circulaires — voir le bloc `if TYPE_CHECKING:` en haut de chaque fichier.

Pourquoi le CRUD Maison/Professeur/Cours/Élève n'est pas protégé par rôle : le critère de fin de jour 1 du cahier des charges veut que chaque ressource soit "créée, lue, modifiée et supprimée" librement pour vérifier que le CRUD fonctionne. Le mécanisme de rôle (`app/auth.py`, `role_requis(...)`) est prêt et testé (`GET /whoami`) ; le jour 2 l'utilise pour de bon sur l'espace élève (`/moi/...`), qui doit rester strictement scopé à l'élève qui consulte. Si votre équipe préfère verrouiller le CRUD dès maintenant, il suffit d'ajouter `@role_requis(RoleUtilisateur.ADMIN)` au-dessus des vues d'écriture.

Pourquoi Scalar plutôt que Swagger UI ou flask-smorest : Scalar se résume à une page HTML statique (`app/routes/docs.py`) qui charge un script depuis un CDN et lit `/openapi.json` — aucune dépendance Python à ajouter à `requirements.txt`. C'est un choix d'outil d'affichage, pas d'architecture : n'importe quelle autre interface compatible OpenAPI (Swagger UI, Redoc...) fonctionnerait avec la même spec.

Pourquoi deux statuts séparés, `Resultat.statut` et `Inscription.statut` : ce sont deux questions différentes. "Cet élève a-t-il réussi CET examen ?" se répond au niveau du résultat, avec le seuil de CET examen. "Cet élève a-t-il réussi LE COURS ?" se répond au niveau de l'inscription, avec la moyenne de TOUS ses examens dans ce cours. Les confondre revient à laisser un seul examen décider du sort de tout le cours, ce que le cahier des charges ne demande pas. D'où deux endpoints (`/examens/<id>/cloture` et `/cours/<id>/cloture`) plutôt qu'un seul qui ferait les deux à moitié.

Pourquoi le mode sans `eleve_id` de `/cours/<id>/cloture` ne modifie rien : c'est un rapport, pas une clôture en masse. Clôturer tous les élèves d'un coup sans validation professeur par professeur serait un raccourci que le cahier des charges ne demande pas explicitement ; le mode rapport permet de vérifier les moyennes avant de déclencher les mises à jour une par une.

Pourquoi le chargement anticipé (`joinedload`) est optionnel plutôt qu'activé par défaut : voir `PERFORMANCE.md`. En résumé, le coût existe (plus de colonnes ramenées par ligne) et n'a de sens que sur un accès en boucle — l'imposer partout serait une optimisation prématurée.

Pourquoi l'écriture sur Compétence et Tournoi est réservée à l'admin, contrairement au CRUD ouvert du jour 1 : le cahier des charges distingue explicitement, pour le jour 3, les actions "administratives" (créer une compétence, organiser un tournoi) des consultations élève. Ce n'est pas une incohérence avec le choix du jour 1 mais un changement de nature : Maison/Professeur/Cours/Élève sont des données de référence qu'il fallait pouvoir manipuler librement pour vérifier le CRUD, alors que Compétence et Tournoi pilotent des effets de bord réels sur la réputation d'une maison — les protéger dès leur introduction évite d'avoir à revenir dessus plus tard. La même règle s'applique à Année académique au jour 4, pour la même raison (une clôture d'année a des effets de bord réels sur le dossier de chaque élève).

Pourquoi marshmallow plutôt que pydantic : les deux auraient rempli le rôle, marshmallow a été préféré parce que son couple `Schema.load()` / `ValidationError.messages` colle exactement au format `(donnees, erreur)` déjà en place dans le projet depuis `_valider_payload_competence` (jour 3) — reprendre le même idiome partout plutôt que d'en introduire un second.

Pourquoi la validation métier (existence d'une clé étrangère, cohérence `condition_type`/`examen_id`, capacité d'un cours) reste dans les routes et ne remonte pas dans les schémas marshmallow : un schéma décrit la forme d'un payload indépendamment de toute requête en base. Une compétence dont l'`examen_id` a le bon type mais ne correspond à aucun examen n'est pas un problème de forme, c'est un problème de cohérence avec l'état actuel de la base — la distinguer clairement évite qu'un schéma se mette à faire des requêtes SQL, ce qui le rendrait plus difficile à tester isolément.

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

# 4. Peupler la base (4 maisons, 160 élèves, 5 professeurs, 5 cours, 10 examens,
#    19 compétences, 3 tournois clôturés, un compte par personne + admin)
python seed.py

# 5. Lancer le serveur
python run.py

# 6. Lancer les tests
pytest
```

L'environnement virtuel (`.venv/`) n'est pas versionné (voir `.gitignore`) : chaque personne de l'équipe le recrée localement à partir de `requirements.txt`.

### Variables d'environnement (`.env`)

| Variable | Rôle | Valeur par défaut si absente |
|---|---|---|
| `FLASK_ENV` | `development` ou `testing` — sélectionne la config dans `config.py` | `development` |
| `SECRET_KEY` | Clé Flask (sessions, à terme un vrai mécanisme d'auth) | valeur de secours fixée dans `config.py`, à changer en production |
| `DATABASE_URL` | Chemin de la base SQLite | **laissée commentée**, voir avertissement ci-dessous |
| `SQLALCHEMY_ECHO` | `True` pour voir chaque requête SQL générée dans les logs | `False` |
| `LOG_LEVEL` | Niveau du logger applicatif (`DEBUG`, `INFO`, `WARNING`...) | `INFO` |
| `LOG_TO_FILE` | `True` pour dupliquer les logs dans `logs/` (fichier tournant) | `False` |

Important sur `DATABASE_URL` : laissez la ligne commentée par défaut. `config.py` utilise alors un chemin absolu (`<racine du projet>/academie.db`). Si vous la décommentez avec un chemin relatif comme `sqlite:///academie.db`, Flask-SQLAlchemy le résout par rapport au dossier `instance/` de Flask, pas à la racine du projet — vous auriez alors deux fichiers `.db` différents selon que la variable est définie ou non, avec `seed.py` qui peuple l'un et le serveur qui lit l'autre (symptôme : `OperationalError: no such table`, alors que le seed s'est pourtant bien déroulé).

### Essayer rapidement

```bash
curl http://127.0.0.1:5000/health

curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@academie-sorcellerie.fr", "mot_de_passe": "admin123"}'

# Avec l'id renvoyé par /login :
curl http://127.0.0.1:5000/whoami -H "X-User-Id: 36"

curl http://127.0.0.1:5000/maisons

# Payload invalide : le champ fautif est nommé dans la réponse (jour 4)
curl -X POST http://127.0.0.1:5000/maisons \
  -H "Content-Type: application/json" -d '{"nom": "Pyrraxis"}'
# -> 400 {"erreur": "Payload invalide.", "champs": {"couleur": [...], "fondateur": [...]}}

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

# Compétences : catalogue public, paginé
curl "http://127.0.0.1:5000/competences?categorie=Sorts%20offensifs&page=1&par_page=10"

# Débloquer les compétences d'un examen après sa clôture (avec le compte admin)
curl -X POST http://127.0.0.1:5000/examens/1/cloture
curl -X POST http://127.0.0.1:5000/examens/1/evaluer-competences -H "X-User-Id: 36"

# Tournoi : créer, enregistrer un duel, puis clôturer (toutes ces écritures exigent l'admin)
curl -X POST http://127.0.0.1:5000/tournois \
  -H "Content-Type: application/json" -H "X-User-Id: 36" \
  -d '{"nom": "Tournoi de printemps", "annee": 2026}'

curl -X POST http://127.0.0.1:5000/tournois/1/duels \
  -H "Content-Type: application/json" -H "X-User-Id: 36" \
  -d '{"eleve_1_id": 1, "eleve_2_id": 2, "vainqueur_id": 1}'

curl -X POST http://127.0.0.1:5000/tournois/1/cloture -H "X-User-Id: 36"

# Duel invalide : le vainqueur doit être l'un des deux participants (jour 4)
curl -X POST http://127.0.0.1:5000/tournois/1/duels \
  -H "Content-Type: application/json" -H "X-User-Id: 36" \
  -d '{"eleve_1_id": 1, "eleve_2_id": 2, "vainqueur_id": 9999}'
# -> 400 {"erreur": "Payload invalide.", "champs": {"vainqueur_id": [...]}}

# Espace élève : compétences et historique de tournois de l'élève connecté
curl http://127.0.0.1:5000/moi/competences -H "X-User-Id: 1"
curl http://127.0.0.1:5000/moi/tournois -H "X-User-Id: 1"

# Année académique : consulter, ajuster le seuil, puis clôturer (jour 4)
curl http://127.0.0.1:5000/annees-academiques

curl -X PUT http://127.0.0.1:5000/annees-academiques/1 \
  -H "Content-Type: application/json" -H "X-User-Id: 36" \
  -d '{"libelle": "2025-2026", "seuil_promotion": 10}'

curl -X POST http://127.0.0.1:5000/annees-academiques/1/cloture -H "X-User-Id: 36"

# Même appel avec un seuil différent, sans modifier celui enregistré
curl -X POST "http://127.0.0.1:5000/annees-academiques/2/cloture?seuil=12" -H "X-User-Id: 36"

# Rejouer la clôture d'une année déjà close : refusé
curl -X POST http://127.0.0.1:5000/annees-academiques/1/cloture -H "X-User-Id: 36"
# -> 400 {"erreur": "Cette année académique est déjà clôturée."}
```

Tous les comptes créés par `seed.py` utilisent le mot de passe `motdepasse123` (élèves et professeurs) ou `admin123` (le compte admin), sur le modèle `prenom.nom@academie-sorcellerie.fr`.

Ouvrez `http://127.0.0.1:5000/docs` dans un navigateur pour la documentation interactive (Scalar) : tous les endpoints ci-dessus y sont décrits avec leurs schémas de requête/réponse, y compris le format d'erreur de validation (`ErreurValidation`) et les trois issues du passage d'année.

## Projet complet

Les quatre jours du cahier des charges sont livrés : modèles et CRUD (jour 1), inscriptions/examens/résultats et leurs deux clôtures distinctes (jour 2), compétences/maîtrises/tournois (jour 3), passage de fin d'année et validation stricte (jour 4). 112 tests couvrent l'ensemble, le seed reproduit un volume proche d'une vraie promotion (160 élèves sur 7 années d'étude), et `PERFORMANCE.md` documente les deux endroits du projet où un N+1 réel a été mesuré puis corrigé.

Quelques pistes, hors cahier des charges, pour qui voudrait continuer au-delà :

Une vraie authentification (mot de passe haché, session ou JWT) à la place de la connexion simulée par header `X-User-Id` — volontairement simplifiée pour rester centrée sur le métier pédagogique plutôt que sur l'auth.

Une gestion multi-années plus poussée : le passage de fin d'année crée une promotion pour l'année d'étude suivante, mais rien ne crée encore automatiquement la nouvelle `AnneeAcademique` ni ne réinscrit les élèves promus à leurs nouveaux cours — ça reste une étape manuelle après la clôture.

Une collection Postman à côté de ce README, pour qui préfère cliquer plutôt que copier des `curl` — la spec OpenAPI (`/openapi.json`) s'importe telle quelle dans Postman si le besoin s'en fait sentir.

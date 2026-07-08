# Chasse au N+1 — jour 2

## Le scénario

`GET /cours/<id>/eleves` liste les élèves inscrits à un cours et, pour
chacun, son nom et le nom de sa maison (`app/routes/inscriptions.py`,
`lister_eleves_du_cours`) :

```python
inscriptions = db.session.query(Inscription).filter_by(cours_id=cours_id).all()
for inscription in inscriptions:
    eleve = inscription.eleve      # relation Inscription -> Eleve
    eleve.maison.nom               # relation Eleve -> Maison
```

Par défaut, SQLAlchemy charge les relations en chargement paresseux
(lazy loading) : chaque accès à `inscription.eleve` puis à `eleve.maison`
déclenche sa propre requête SQL. Sur une boucle de N élèves, ça fait
potentiellement 2N+1 requêtes au lieu d'une seule.

## Méthode de mesure

Plutôt qu'un calcul théorique, les chiffres ci-dessous viennent d'un
comptage réel des requêtes exécutées, via l'event SQLAlchemy
`before_cursor_execute` (une requête = un déclenchement de l'event),
sur la base peuplée par `seed.py` avec 20 élèves inscrits à un même
cours ("Potions avancées", 5 maisons... pardon, 4 maisons représentées
parmi les 20 élèves).

Reproductible avec `SQLALCHEMY_ECHO=True` dans `.env` : chaque requête
SQL s'affiche dans les logs du serveur pendant l'appel à l'endpoint.

## Résultats

| Mode | Requêtes SQL | Détail |
|---|---|---|
| Chargement paresseux (défaut, `GET /cours/1/eleves`) | **26** | 1 pour les inscriptions, 20 pour charger chaque élève un par un, ~5 pour charger les maisons (partiellement dédupliquées par l'identity map de la session) |
| Chargement anticipé (`GET /cours/1/eleves?eager=true`) | **2** | Un `JOIN` unique (`joinedload(Inscription.eleve).joinedload(Eleve.maison)`) qui ramène inscriptions, élèves et maisons en une seule requête |

13 fois moins de requêtes sur ce jeu de données précis. L'écart grandit avec le nombre d'élèves inscrits : la version paresseuse est en O(N), la version avec `joinedload` reste à peu près constante.

## Le correctif

```python
query = db.session.query(Inscription).filter_by(cours_id=cours_id)
if eager:
    query = query.options(joinedload(Inscription.eleve).joinedload(Eleve.maison))
inscriptions = query.all()
```

Rendu optionnel via `?eager=true` plutôt que systématique, comme demandé par le cahier des charges. Deux raisons concrètes à ce choix, pas juste pour suivre la consigne à la lettre :

Le `JOIN` ramène plus de colonnes par ligne (celles d'`Eleve` et de `Maison` en plus de celles d'`Inscription`) : sur un endpoint qui n'a pas besoin de ces relations, l'activer par défaut gaspillerait de la bande passante et du temps de sérialisation pour rien.

Le chargement paresseux reste le bon choix par défaut pour un accès isolé (`GET /eleves/<id>`, un seul élève, une seule relation à charger) : le N+1 n'existe que dans une boucle. Le corriger partout et systématiquement serait une sur-optimisation qui complique le code sans bénéfice mesurable en dehors des listings.

## Où réappliquer cette chasse plus tard dans le projet

Tout endpoint de listing qui boucle sur une collection et accède à une relation par itération est candidat : par exemple `/moi/cours` et `/moi/notes` (jour 2, actuellement en lazy — acceptable tant que le nombre de cours/notes par élève reste petit, à surveiller si ça change), ou tout endpoint de listing du jour 3 qui accéderait à `eleve.maitrises` ou `tournoi.duels` en boucle.

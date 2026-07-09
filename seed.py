"""
Point d'entrée du script de seed : `python seed.py`.

Rejouable sans dupliquer ni casser les données (critère du jour 4) : chaque
entité est cherchée par un champ qui l'identifie sans ambiguïté avant
d'être créée (get_or_create), plutôt que recréée aveuglément à chaque
exécution. Relancer ce script dix fois de suite doit toujours laisser
exactement le même nombre de lignes.

Limite connue de get_or_create : si vous changez une valeur par défaut
(ex. capacite_max d'un cours) après un premier seed, relancer le script
ne met PAS à jour la ligne déjà existante — get_or_create ne fait que
lire ou créer, jamais mettre à jour. Sur une base déjà peuplée avec une
version antérieure de ce fichier, supprimez le fichier .db (ou la base
de test) avant de relancer si vous voulez repartir sur les nouvelles
valeurs.

Volume réaliste (jour 4) : 160 élèves plutôt que 30, deux examens par
cours (un devoir de mi-parcours en plus de l'examen final), des
inscriptions et des résultats réellement saisis et clôturés (le seed
d'avant le jour 4 laissait ça à la charge des tests et de l'usage manuel),
plus trois tournois déjà joués et clôturés pour disposer d'un historique
de compétences débloquées dès le premier lancement.
"""

import random
from datetime import date, datetime

from app import create_app
from app.extensions import db
from app.dal.models import (
    AnneeAcademique,
    Competence,
    Cours,
    Duel,
    Eleve,
    Examen,
    Inscription,
    Maison,
    Maitrise,
    Professeur,
    Resultat,
    Tournoi,
    Utilisateur,
)
from app.dal.models.enums import (
    RoleUtilisateur,
    SourceDeblocage,
    StatutEleve,
    StatutInscription,
    StatutResultat,
)
from app.routes.tournois import POINTS_REPUTATION_VICTOIRE_TOURNOI

app = create_app()

# Seed fixe : deux exécutions produisent exactement les mêmes notes, donc
# les mêmes décisions de clôture — indispensable pour que "rejouable sans
# casser les données" veuille aussi dire "rejouable sans résultat différent".
RNG = random.Random(2026)


def get_or_create(model, lookup, defaults=None):
    """Cherche une ligne selon `lookup` ; la crée avec `lookup` + `defaults`
    si elle n'existe pas encore. `lookup` doit porter sur un champ qui
    identifie la ligne sans ambiguïté (idéalement une colonne unique).
    """
    instance = db.session.query(model).filter_by(**lookup).one_or_none()
    if instance is not None:
        return instance

    instance = model(**lookup, **(defaults or {}))
    db.session.add(instance)
    db.session.flush()  # attribue l'id sans committer toute la transaction
    return instance


def note_aleatoire():
    """Note entre 0 et 20, tirée d'une gaussienne centrée à 12.5 et bornée
    aux deux extrémités — volontairement pas une loi uniforme, pour que la
    distribution ressemble à une vraie classe (beaucoup de notes moyennes,
    peu d'extrêmes) plutôt qu'un bruit plat.
    """
    return round(min(20.0, max(0.0, RNG.gauss(12.5, 4.0))), 1)


MAISONS = [
    {
        "nom": "Pyrraxis",
        "couleur": "Rouge et or",
        "fondateur": "Ignatius Brasier",
        "valeurs": "Courage, audace",
    },
    {
        "nom": "Umbraliss",
        "couleur": "Vert et argent",
        "fondateur": "Morgana Nightshade",
        "valeurs": "Ambition, ruse",
    },
    {
        "nom": "Sylvebranche",
        "couleur": "Bleu et bronze",
        "fondateur": "Elowen Fontaine",
        "valeurs": "Sagesse, curiosité",
    },
    {
        "nom": "Terrefeuille",
        "couleur": "Jaune et noir",
        "fondateur": "Cedric Aubépine",
        "valeurs": "Loyauté, patience",
    },
]

PROFESSEURS = [
    {"nom": "Théodore Vance", "matiere_enseignee": "Potions", "anciennete": 15},
    {"nom": "Isolde Marchetti", "matiere_enseignee": "Sortilèges de défense", "anciennete": 8},
    {"nom": "Percival Ashworth", "matiere_enseignee": "Métamorphose", "anciennete": 22},
    {"nom": "Ondine Lacroix", "matiere_enseignee": "Divination", "anciennete": 5},
    {"nom": "Magnus Ferro", "matiere_enseignee": "Sortilèges offensifs", "anciennete": 12},
]

# capacite_max relevée par rapport aux jours 1-3 (25-30) pour absorber le
# volume réaliste du jour 4 (160 élèves, jusqu'à 3 cours chacun) sans
# provoquer de "cours complet" pendant le seed lui-même.
COURS = [
    {
        "intitule": "Potions avancées",
        "niveau_requis": 4,
        "capacite_max": 150,
        "professeur": "Théodore Vance",
    },
    {
        "intitule": "Défense élémentaire",
        "niveau_requis": 1,
        "capacite_max": 150,
        "professeur": "Isolde Marchetti",
    },
    {
        "intitule": "Métamorphose intermédiaire",
        "niveau_requis": 3,
        "capacite_max": 150,
        "professeur": "Percival Ashworth",
    },
    {
        "intitule": "Divination des augures",
        "niveau_requis": 5,
        "capacite_max": 150,
        "professeur": "Ondine Lacroix",
    },
    {
        "intitule": "Sortilèges de combat",
        "niveau_requis": 2,
        "capacite_max": 150,
        "professeur": "Magnus Ferro",
    },
]

# Deux examens par cours (jour 4 : "plusieurs examens") : un devoir de
# mi-parcours au seuil plus bas, et l'examen final déjà présent depuis le
# jour 1/3, seul référencé par les compétences à condition "examen" (voir
# COMPETENCES plus bas — la maîtrise se gagne sur la performance finale,
# pas sur un galop d'essai).
EXAMENS = [
    {
        "cours": "Potions avancées",
        "titre": "Devoir de mi-parcours de potions",
        "date": date(2026, 2, 10),
        "seuil_reussite": 8.0,
    },
    {
        "cours": "Potions avancées",
        "titre": "Examen final de potions",
        "date": date(2026, 5, 15),
        "seuil_reussite": 10.0,
    },
    {
        "cours": "Défense élémentaire",
        "titre": "Devoir de mi-parcours de défense élémentaire",
        "date": date(2026, 2, 11),
        "seuil_reussite": 8.0,
    },
    {
        "cours": "Défense élémentaire",
        "titre": "Examen final de défense élémentaire",
        "date": date(2026, 5, 16),
        "seuil_reussite": 10.0,
    },
    {
        "cours": "Métamorphose intermédiaire",
        "titre": "Devoir de mi-parcours de métamorphose",
        "date": date(2026, 2, 12),
        "seuil_reussite": 8.0,
    },
    {
        "cours": "Métamorphose intermédiaire",
        "titre": "Examen final de métamorphose",
        "date": date(2026, 5, 17),
        "seuil_reussite": 10.0,
    },
    {
        "cours": "Divination des augures",
        "titre": "Devoir de mi-parcours de divination",
        "date": date(2026, 2, 13),
        "seuil_reussite": 8.0,
    },
    {
        "cours": "Divination des augures",
        "titre": "Examen final de divination",
        "date": date(2026, 5, 18),
        "seuil_reussite": 10.0,
    },
    {
        "cours": "Sortilèges de combat",
        "titre": "Devoir de mi-parcours de sortilèges offensifs",
        "date": date(2026, 2, 14),
        "seuil_reussite": 8.0,
    },
    {
        "cours": "Sortilèges de combat",
        "titre": "Examen final de sortilèges offensifs",
        "date": date(2026, 5, 19),
        "seuil_reussite": 10.0,
    },
]

# 19 compétences (le cahier des charges en demande 15 à 20) : 15 à
# condition "examen" (3 par examen final, avec des note_min variées pour
# représenter des niveaux de maîtrise différents) et 4 à condition
# "tournoi" (débloquées au vainqueur d'un tournoi, quel qu'il soit — voir
# POST /tournois/<id>/cloture).
COMPETENCES = [
    # Potions
    {
        "nom": "Dosage de précision",
        "categorie": "Potions",
        "description": "Prépare une potion sans dévier d'un gramme sur les proportions.",
        "condition": ("examen", "Examen final de potions", 10),
    },
    {
        "nom": "Philtre de Félicité",
        "categorie": "Potions",
        "description": "Maîtrise la préparation du philtre de bonheur temporaire.",
        "condition": ("examen", "Examen final de potions", 14),
    },
    {
        "nom": "Élixir de Polynectar simplifié",
        "categorie": "Potions",
        "description": "Version allégée du Polynectar, réservée aux meilleurs élèves.",
        "condition": ("examen", "Examen final de potions", 17),
    },
    # Sorts défensifs
    {
        "nom": "Bouclier de Protego",
        "categorie": "Sorts défensifs",
        "description": "Lève un bouclier magique capable d'absorber un sort simple.",
        "condition": ("examen", "Examen final de défense élémentaire", 10),
    },
    {
        "nom": "Contre-sort réflexe",
        "categorie": "Sorts défensifs",
        "description": "Renvoie un sort adverse sans temps de préparation.",
        "condition": ("examen", "Examen final de défense élémentaire", 13),
    },
    {
        "nom": "Barrière de Fumée Runique",
        "categorie": "Sorts défensifs",
        "description": "Dissimule sa position derrière un écran runique temporaire.",
        "condition": ("examen", "Examen final de défense élémentaire", 16),
    },
    # Métamorphose
    {
        "nom": "Transfiguration d'objet simple",
        "categorie": "Métamorphose",
        "description": "Transforme un petit objet inanimé en un autre.",
        "condition": ("examen", "Examen final de métamorphose", 10),
    },
    {
        "nom": "Métamorphose animale partielle",
        "categorie": "Métamorphose",
        "description": "Modifie une partie de son corps en trait animal, temporairement.",
        "condition": ("examen", "Examen final de métamorphose", 14),
    },
    {
        "nom": "Animagus en formation",
        "categorie": "Métamorphose",
        "description": "Entame la transformation complète en forme animale.",
        "condition": ("examen", "Examen final de métamorphose", 18),
    },
    # Divination
    {
        "nom": "Lecture des feuilles de thé",
        "categorie": "Divination",
        "description": "Interprète les formes laissées par les feuilles de thé.",
        "condition": ("examen", "Examen final de divination", 10),
    },
    {
        "nom": "Boule de cristal, premiers signes",
        "categorie": "Divination",
        "description": "Distingue les premières images significatives dans une boule de cristal.",
        "condition": ("examen", "Examen final de divination", 13),
    },
    {
        "nom": "Prémonition guidée",
        "categorie": "Divination",
        "description": "Provoque volontairement une prémonition de courte portée.",
        "condition": ("examen", "Examen final de divination", 17),
    },
    # Sorts offensifs
    {
        "nom": "Sort de Stupéfixion",
        "categorie": "Sorts offensifs",
        "description": "Immobilise un adversaire à distance de sécurité.",
        "condition": ("examen", "Examen final de sortilèges offensifs", 10),
    },
    {
        "nom": "Incantation de la Foudre Runique",
        "categorie": "Sorts offensifs",
        "description": "Décharge un trait de foudre canalisé par une rune de combat.",
        "condition": ("examen", "Examen final de sortilèges offensifs", 14),
    },
    {
        "nom": "Rafale d'Éclats Arcaniques",
        "categorie": "Sorts offensifs",
        "description": "Enchaîne plusieurs projectiles magiques en une seule incantation.",
        "condition": ("examen", "Examen final de sortilèges offensifs", 17),
    },
    # Tournoi — débloquées au vainqueur de n'importe quel tournoi clôturé.
    {
        "nom": "Titre de Champion du Tournoi",
        "categorie": "Tournoi",
        "description": "Reconnaissance officielle accordée au vainqueur d'un tournoi.",
        "condition": ("tournoi", None, None),
    },
    {
        "nom": "Posture du Duelliste Aguerri",
        "categorie": "Tournoi",
        "description": "Maintien et déplacement optimisés pour l'enchaînement de duels.",
        "condition": ("tournoi", None, None),
    },
    {
        "nom": "Aura de Prestige",
        "categorie": "Tournoi",
        "description": "Confiance et prestance reconnues après une victoire marquante.",
        "condition": ("tournoi", None, None),
    },
    {
        "nom": "Sang-froid du Champion",
        "categorie": "Tournoi",
        "description": "Capacité à garder son calme après une série de duels intenses.",
        "condition": ("tournoi", None, None),
    },
]

# 40 prénoms x 8 noms de famille = 320 combinaisons possibles, largement
# assez pour les 160 élèves du jour 4 sans retomber deux fois sur le même
# nom complet (voir nom_complet_eleve ci-dessous).
PRENOMS = [
    "Alaric", "Brielle", "Cassian", "Delphine", "Emrys", "Fiora", "Gareth", "Helios",
    "Iris", "Jorah", "Kiara", "Leander", "Maelle", "Noam", "Orla", "Perceval",
    "Quintus", "Romy", "Silas", "Tamsin", "Ulric", "Vesper", "Wynn", "Xela",
    "Yorick", "Zora", "Aldric", "Briar", "Corvin", "Elara", "Faelan", "Ginevra",
    "Hadrien", "Isolde", "Joachim", "Kessia", "Lysandre", "Morwenna", "Neven", "Ottavia",
]

NOMS_DE_FAMILLE = [
    "Corvenoire", "Ashford", "Duvent", "Roussel",
    "Fontaine", "Nightshade", "Brasier", "Marchetti",
]

FAMILIERS = ["Chat", "Hibou", "Crapaud", "Rat", "Faucon", None]

NB_ELEVES = 160


def nom_complet_eleve(i):
    prenom = PRENOMS[i % len(PRENOMS)]
    nom = NOMS_DE_FAMILLE[(i // len(PRENOMS)) % len(NOMS_DE_FAMILLE)]
    return f"{prenom} {nom}"


def _cours_a_suivre(eleve_dict, cours_par_intitule):
    """Détermine les cours qu'un élève suit, à partir de son année d'étude
    et du niveau requis de chaque cours : tous les cours dont le niveau
    requis ne dépasse pas son année, jusqu'à 3 (pour rester réaliste, pas
    un élève inscrit partout), en privilégiant les cours de niveau le plus
    proche de son année actuelle.
    """
    eligibles = [c for c in cours_par_intitule.values() if c.niveau_requis <= eleve_dict["annee_etude"]]
    eligibles.sort(key=lambda c: c.niveau_requis, reverse=True)
    return eligibles[:3]


def _generer_duels_tournoi(participants):
    """participants : au moins 4 objets Eleve. Construit un petit bracket
    déterministe où participants[0] (le favori) remporte strictement plus
    de duels que quiconque d'autre — pas de risque d'égalité à la clôture.
    Retourne une liste de tuples (eleve_1, eleve_2, vainqueur).
    """
    favori, *autres = participants
    duels = [(favori, adversaire, favori) for adversaire in autres]
    if len(autres) >= 2:
        duels.append((autres[0], autres[1], autres[0]))
    return duels


def run():
    with app.app_context():
        db.create_all()

        annee = get_or_create(
            AnneeAcademique,
            lookup={"libelle": "2025-2026"},
            defaults={"seuil_promotion": 10.0},
        )

        maisons = {}
        for data in MAISONS:
            nom = data["nom"]
            maisons[nom] = get_or_create(
                Maison,
                lookup={"nom": nom},
                defaults={k: v for k, v in data.items() if k != "nom"},
            )

        professeurs = {}
        for data in PROFESSEURS:
            nom = data["nom"]
            professeurs[nom] = get_or_create(
                Professeur,
                lookup={"nom": nom},
                defaults={k: v for k, v in data.items() if k != "nom"},
            )

        cours_par_intitule = {}
        for data in COURS:
            cours_par_intitule[data["intitule"]] = get_or_create(
                Cours,
                lookup={"intitule": data["intitule"]},
                defaults={
                    "niveau_requis": data["niveau_requis"],
                    "capacite_max": data["capacite_max"],
                    "professeur_id": professeurs[data["professeur"]].id,
                    "annee_academique_id": annee.id,
                },
            )

        examens_par_titre = {}
        for data in EXAMENS:
            examens_par_titre[data["titre"]] = get_or_create(
                Examen,
                lookup={"titre": data["titre"]},
                defaults={
                    "date": data["date"],
                    "seuil_reussite": data["seuil_reussite"],
                    "cours_id": cours_par_intitule[data["cours"]].id,
                },
            )

        for data in COMPETENCES:
            condition_kind, examen_titre, note_min = data["condition"]
            if condition_kind == "examen":
                defaults = {
                    "categorie": data["categorie"],
                    "description": data["description"],
                    "condition_type": SourceDeblocage.EXAMEN,
                    "examen_id": examens_par_titre[examen_titre].id,
                    "note_min": note_min,
                }
            else:
                defaults = {
                    "categorie": data["categorie"],
                    "description": data["description"],
                    "condition_type": SourceDeblocage.TOURNOI,
                }
            get_or_create(Competence, lookup={"nom": data["nom"]}, defaults=defaults)

        # --- Élèves + comptes -------------------------------------------
        noms_maisons = list(maisons.keys())
        eleves_crees = []
        for i in range(NB_ELEVES):
            nom_complet = nom_complet_eleve(i)
            eleve_dict = {"annee_etude": (i % 7) + 1}
            eleve = get_or_create(
                Eleve,
                lookup={"nom": nom_complet},
                defaults={
                    "annee_etude": eleve_dict["annee_etude"],
                    "maison_id": maisons[noms_maisons[i % len(noms_maisons)]].id,
                    "familier": FAMILIERS[i % len(FAMILIERS)],
                    "statut": StatutEleve.ACTIF,
                },
            )
            eleves_crees.append(eleve)

            slug = f"{nom_complet.lower().replace(' ', '.')}.{i}"
            get_or_create(
                Utilisateur,
                lookup={"email": f"{slug}@academie-sorcellerie.fr"},
                defaults={
                    "mot_de_passe": "motdepasse123",
                    "role": RoleUtilisateur.ELEVE,
                    "eleve_id": eleve.id,
                },
            )

        for data in PROFESSEURS:
            professeur = professeurs[data["nom"]]
            slug = data["nom"].lower().replace(" ", ".")
            get_or_create(
                Utilisateur,
                lookup={"email": f"{slug}@academie-sorcellerie.fr"},
                defaults={
                    "mot_de_passe": "motdepasse123",
                    "role": RoleUtilisateur.PROFESSEUR,
                    "professeur_id": professeur.id,
                },
            )

        get_or_create(
            Utilisateur,
            lookup={"email": "admin@academie-sorcellerie.fr"},
            defaults={"mot_de_passe": "admin123", "role": RoleUtilisateur.ADMIN},
        )

        # --- Inscriptions + résultats -------------------------------------
        # Chaque élève actif s'inscrit aux cours de son niveau (voir
        # _cours_a_suivre), puis reçoit une note à chaque examen de ces
        # cours. Boucle par élève assumée ici (le seed n'est pas un
        # endpoint HTTP mesuré dans PERFORMANCE.md), mais les clôtures
        # ci-dessous, elles, sont faites en requêtes groupées.
        for i, eleve in enumerate(eleves_crees):
            annee_etude = (i % 7) + 1
            for cours in _cours_a_suivre({"annee_etude": annee_etude}, cours_par_intitule):
                get_or_create(
                    Inscription,
                    lookup={"eleve_id": eleve.id, "cours_id": cours.id},
                    defaults={"date_inscription": date(2025, 9, 1), "statut": StatutInscription.INSCRIT},
                )
                for examen in cours.examens:
                    get_or_create(
                        Resultat,
                        lookup={"eleve_id": eleve.id, "examen_id": examen.id},
                        defaults={"note": note_aleatoire()},
                    )

        db.session.flush()

        # --- Clôture des examens (statut réussi/échec par examen) --------
        for examen in examens_par_titre.values():
            resultats = db.session.query(Resultat).filter_by(examen_id=examen.id).all()
            for resultat in resultats:
                resultat.statut = (
                    StatutResultat.REUSSI
                    if resultat.note >= examen.seuil_reussite
                    else StatutResultat.ECHEC
                )

        # --- Clôture des cours (statut de l'inscription) ------------------
        for cours in cours_par_intitule.values():
            inscriptions = db.session.query(Inscription).filter_by(cours_id=cours.id).all()
            for inscription in inscriptions:
                resultats = (
                    db.session.query(Resultat)
                    .join(Examen, Resultat.examen_id == Examen.id)
                    .filter(Examen.cours_id == cours.id, Resultat.eleve_id == inscription.eleve_id)
                    .all()
                )
                if not resultats:
                    continue
                moyenne = sum(r.note for r in resultats) / len(resultats)
                seuil_moyen = sum(r.examen.seuil_reussite for r in resultats) / len(resultats)
                inscription.statut = (
                    StatutInscription.VALIDE if moyenne >= seuil_moyen else StatutInscription.EN_COURS
                )

        db.session.flush()

        # --- Déblocage des compétences à condition "examen" ---------------
        competences_examen = (
            db.session.query(Competence).filter_by(condition_type=SourceDeblocage.EXAMEN).all()
        )
        for competence in competences_examen:
            resultats = db.session.query(Resultat).filter_by(examen_id=competence.examen_id).all()
            for resultat in resultats:
                if resultat.note < competence.note_min:
                    continue
                get_or_create(
                    Maitrise,
                    lookup={"eleve_id": resultat.eleve_id, "competence_id": competence.id},
                    defaults={
                        "date_obtention": date(2026, 5, 20),
                        "source": SourceDeblocage.EXAMEN,
                        "source_examen_id": competence.examen_id,
                    },
                )

        # --- Tournois déjà joués et clôturés -------------------------------
        # Trois tournois sur trois années différentes, chacun avec un petit
        # bracket de duels (voir _generer_duels_tournoi) et un vainqueur sans
        # ambiguïté. Le bloc entier est sauté si le tournoi a déjà ses duels
        # (rejeu du script) : Duel n'a pas de contrainte unique en base, donc
        # c'est cette vérification-là qui garantit l'idempotence ici, plutôt
        # qu'un get_or_create par duel.
        TOURNOIS = [
            {"nom": "Tournoi de printemps", "annee": 2024, "participants": eleves_crees[0:4]},
            {"nom": "Tournoi d'automne", "annee": 2025, "participants": eleves_crees[4:8]},
            {"nom": "Tournoi de printemps", "annee": 2026, "participants": eleves_crees[8:12]},
        ]
        for i, data in enumerate(TOURNOIS):
            maison_organisatrice = maisons[noms_maisons[i % len(noms_maisons)]]
            tournoi = get_or_create(
                Tournoi,
                lookup={"nom": data["nom"], "annee": data["annee"]},
                defaults={"maison_organisatrice_id": maison_organisatrice.id},
            )
            if tournoi.duels:
                continue

            for eleve_1, eleve_2, vainqueur in _generer_duels_tournoi(data["participants"]):
                db.session.add(
                    Duel(
                        tournoi_id=tournoi.id,
                        eleve_1_id=eleve_1.id,
                        eleve_2_id=eleve_2.id,
                        vainqueur_id=vainqueur.id,
                    )
                )
            db.session.flush()

            duels = db.session.query(Duel).filter_by(tournoi_id=tournoi.id).all()
            victoires = {}
            for duel in duels:
                victoires[duel.vainqueur_id] = victoires.get(duel.vainqueur_id, 0) + 1
            vainqueur_id = max(victoires, key=victoires.get)
            vainqueur = db.session.get(Eleve, vainqueur_id)

            tournoi.vainqueur_eleve_id = vainqueur_id
            tournoi.cloture_le = datetime.utcnow()

            competences_tournoi = (
                db.session.query(Competence).filter_by(condition_type=SourceDeblocage.TOURNOI).all()
            )
            for competence in competences_tournoi:
                get_or_create(
                    Maitrise,
                    lookup={"eleve_id": vainqueur_id, "competence_id": competence.id},
                    defaults={
                        "date_obtention": date(data["annee"], 6, 1),
                        "source": SourceDeblocage.TOURNOI,
                        "source_tournoi_id": tournoi.id,
                    },
                )

            vainqueur.maison.reputation += POINTS_REPUTATION_VICTOIRE_TOURNOI

        db.session.commit()

        nb_inscriptions = db.session.query(Inscription).count()
        nb_resultats = db.session.query(Resultat).count()
        nb_maitrises = db.session.query(Maitrise).count()
        nb_tournois = db.session.query(Tournoi).count()

        print(
            f"Seed terminé : {len(MAISONS)} maisons, {len(PROFESSEURS)} professeurs, "
            f"{len(COURS)} cours, {len(EXAMENS)} examens, {len(COMPETENCES)} compétences, "
            f"{NB_ELEVES} élèves, {db.session.query(Utilisateur).count()} utilisateurs, "
            f"{nb_inscriptions} inscriptions, {nb_resultats} résultats, "
            f"{nb_tournois} tournois clôturés, {nb_maitrises} maîtrises débloquées."
        )


if __name__ == "__main__":
    run()

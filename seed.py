"""
Point d'entrée du script de seed : `python seed.py`.

Rejouable sans dupliquer ni casser les données (critère du jour 4) : chaque
entité est cherchée par un champ qui l'identifie sans ambiguïté avant
d'être créée (get_or_create), plutôt que recréée aveuglément à chaque
exécution. Relancer ce script dix fois de suite doit toujours laisser
exactement 4 maisons, pas 40.
"""

from datetime import date

from app import create_app
from app.extensions import db
from app.models import (
    AnneeAcademique,
    Competence,
    Cours,
    Eleve,
    Examen,
    Maison,
    Professeur,
    Utilisateur,
)
from app.models.enums import RoleUtilisateur, SourceDeblocage, StatutEleve

app = create_app()


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

COURS = [
    {
        "intitule": "Potions avancées",
        "niveau_requis": 4,
        "capacite_max": 25,
        "professeur": "Théodore Vance",
    },
    {
        "intitule": "Défense élémentaire",
        "niveau_requis": 1,
        "capacite_max": 30,
        "professeur": "Isolde Marchetti",
    },
    {
        "intitule": "Métamorphose intermédiaire",
        "niveau_requis": 3,
        "capacite_max": 20,
        "professeur": "Percival Ashworth",
    },
    {
        "intitule": "Divination des augures",
        "niveau_requis": 5,
        "capacite_max": 15,
        "professeur": "Ondine Lacroix",
    },
    {
        "intitule": "Sortilèges de combat",
        "niveau_requis": 2,
        "capacite_max": 25,
        "professeur": "Magnus Ferro",
    },
]

# 30 élèves, répartis ensuite sur les 7 années et les 4 maisons par simple
# rotation (voir run()) plutôt que par une affectation choisie au cas par
# cas : suffisant pour un jeu de données de test.
ELEVES = [
    "Alaric Corvenoire", "Brielle Ashford", "Cassian Duvent", "Delphine Roussel",
    "Emrys Fontaine", "Fiora Nightshade", "Gareth Aubépine", "Helios Brasier",
    "Iris Marchetti", "Jorah Sylvain", "Kiara Ferro", "Leander Vance",
    "Maelle Lacroix", "Noam Ashworth", "Orla Winterbourne", "Perceval Grisaille",
    "Quintus Rochenoire", "Romy Delacroix", "Silas Aubert", "Tamsin Cendrefleur",
    "Ulric Montfort", "Vesper Aldenoire", "Wynn Solenne", "Xela Bramebois",
    "Yorick Vasseur", "Zora Lunevent", "Aldric Perrenoud", "Briar Castellan",
    "Corvin Delacroix", "Elara Songdor",
]

FAMILIERS = ["Chat", "Hibou", "Crapaud", "Rat", "Faucon", None]

# Un examen "de référence" par cours, seulement pour donner aux compétences
# à condition "examen" (ci-dessous) quelque chose de réel à référencer.
# Le jeu d'inscriptions/résultats qui donnerait un sens pédagogique complet
# à ces examens reste construit à la volée par les tests et par l'usage
# manuel de l'API (voir jour 2) — ce n'est pas le rôle du seed jour 1/3.
EXAMENS = [
    {
        "cours": "Potions avancées",
        "titre": "Examen final de potions",
        "date": date(2026, 5, 15),
        "seuil_reussite": 10.0,
    },
    {
        "cours": "Défense élémentaire",
        "titre": "Examen final de défense élémentaire",
        "date": date(2026, 5, 16),
        "seuil_reussite": 10.0,
    },
    {
        "cours": "Métamorphose intermédiaire",
        "titre": "Examen final de métamorphose",
        "date": date(2026, 5, 17),
        "seuil_reussite": 10.0,
    },
    {
        "cours": "Divination des augures",
        "titre": "Examen final de divination",
        "date": date(2026, 5, 18),
        "seuil_reussite": 10.0,
    },
    {
        "cours": "Sortilèges de combat",
        "titre": "Examen final de sortilèges offensifs",
        "date": date(2026, 5, 19),
        "seuil_reussite": 10.0,
    },
]

# 18 compétences (le cahier des charges en demande 15 à 20) : 14 à
# condition "examen" (2-3 par examen ci-dessus, avec des note_min
# variées pour représenter des niveaux de maîtrise différents) et 4 à
# condition "tournoi" (débloquées au vainqueur d'un tournoi, quel qu'il
# soit — voir POST /tournois/<id>/cloture).
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

        cours = {}
        for data in COURS:
            cours[data["intitule"]] = get_or_create(
                Cours,
                lookup={"intitule": data["intitule"]},
                defaults={
                    "niveau_requis": data["niveau_requis"],
                    "capacite_max": data["capacite_max"],
                    "professeur_id": professeurs[data["professeur"]].id,
                    "annee_academique_id": annee.id,
                },
            )

        examens = {}
        for data in EXAMENS:
            examens[data["titre"]] = get_or_create(
                Examen,
                lookup={"titre": data["titre"]},
                defaults={
                    "date": data["date"],
                    "seuil_reussite": data["seuil_reussite"],
                    "cours_id": cours[data["cours"]].id,
                },
            )

        for data in COMPETENCES:
            condition_kind, examen_titre, note_min = data["condition"]
            if condition_kind == "examen":
                defaults = {
                    "categorie": data["categorie"],
                    "description": data["description"],
                    "condition_type": SourceDeblocage.EXAMEN,
                    "examen_id": examens[examen_titre].id,
                    "note_min": note_min,
                }
            else:
                defaults = {
                    "categorie": data["categorie"],
                    "description": data["description"],
                    "condition_type": SourceDeblocage.TOURNOI,
                }
            get_or_create(Competence, lookup={"nom": data["nom"]}, defaults=defaults)

        noms_maisons = list(maisons.keys())
        for i, nom_complet in enumerate(ELEVES):
            eleve = get_or_create(
                Eleve,
                lookup={"nom": nom_complet},
                defaults={
                    "annee_etude": (i % 7) + 1,
                    "maison_id": maisons[noms_maisons[i % len(noms_maisons)]].id,
                    "familier": FAMILIERS[i % len(FAMILIERS)],
                    "statut": StatutEleve.ACTIF,
                },
            )
            slug = nom_complet.lower().replace(" ", ".")
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

        db.session.commit()

        print(
            f"Seed terminé : {len(MAISONS)} maisons, {len(PROFESSEURS)} professeurs, "
            f"{len(COURS)} cours, {len(EXAMENS)} examens, {len(COMPETENCES)} compétences, "
            f"{len(ELEVES)} élèves, {db.session.query(Utilisateur).count()} utilisateurs."
        )


if __name__ == "__main__":
    run()

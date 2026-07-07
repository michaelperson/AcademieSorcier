"""
Point d'entrée du script de seed : `python seed.py`.

Rejouable sans dupliquer ni casser les données (critère du jour 4) : chaque
entité est cherchée par un champ qui l'identifie sans ambiguïté avant
d'être créée (get_or_create), plutôt que recréée aveuglément à chaque
exécution. Relancer ce script dix fois de suite doit toujours laisser
exactement 4 maisons, pas 40.
"""

from app import create_app
from app.extensions import db
from app.models import (
    AnneeAcademique,
    Cours,
    Eleve,
    Maison,
    Professeur,
    Utilisateur,
)
from app.models.enums import RoleUtilisateur, StatutEleve

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

        for data in COURS:
            get_or_create(
                Cours,
                lookup={"intitule": data["intitule"]},
                defaults={
                    "niveau_requis": data["niveau_requis"],
                    "capacite_max": data["capacite_max"],
                    "professeur_id": professeurs[data["professeur"]].id,
                    "annee_academique_id": annee.id,
                },
            )

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
            f"{len(COURS)} cours, {len(ELEVES)} élèves, "
            f"{db.session.query(Utilisateur).count()} utilisateurs."
        )


if __name__ == "__main__":
    run()

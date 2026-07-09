"""
CRUD sur Cours. Validation stricte (jour 4) via CoursSchema pour les
types et bornes ; l'existence du professeur référencé et le rattachement
à l'année académique restent vérifiés ici, après le schéma, puisque ce
sont des questions d'état de la base et non de forme du payload.

Sortie typée (bonus) : voir app/dal/dto/cours.py::CoursDTO.
"""

from flask import Blueprint, jsonify, request

from app.dal.dto import CoursDTO, vers_dict
from app.extensions import db
from app.dal.models import AnneeAcademique, Cours, Professeur
from app.schemas import CoursSchema
from app.validation import valider

cours_bp = Blueprint("cours", __name__, url_prefix="/cours")


def _construire_dto(cours: Cours) -> CoursDTO:
    return CoursDTO(
        id=cours.id,
        intitule=cours.intitule,
        niveau_requis=cours.niveau_requis,
        capacite_max=cours.capacite_max,
        professeur_id=cours.professeur_id,
        annee_academique_id=cours.annee_academique_id,
    )


def _serialize(cours: Cours) -> dict:
    return vers_dict(_construire_dto(cours))


@cours_bp.get("")
def lister_cours():
    cours = db.session.query(Cours).order_by(Cours.intitule).all()
    return jsonify([_serialize(c) for c in cours]), 200


@cours_bp.get("/<int:cours_id>")
def obtenir_cours(cours_id):
    cours = db.session.get(Cours, cours_id)
    if cours is None:
        return jsonify({"erreur": f"Cours {cours_id} introuvable."}), 404
    return jsonify(_serialize(cours)), 200


@cours_bp.post("")
def creer_cours():
    donnees, erreur = valider(CoursSchema(), request.get_json(silent=True))
    if erreur:
        return erreur

    professeur = db.session.get(Professeur, donnees["professeur_id"])
    if professeur is None:
        return jsonify({"erreur": f"Professeur {donnees['professeur_id']} introuvable."}), 400

    # L'année académique n'est pas encore exposée en écriture par une
    # ressource dédiée à ce stade du projet : on rattache le cours à
    # l'année la plus récente si elle existe déjà (créée par seed.py),
    # ou on refuse la création sinon.
    annee = db.session.query(AnneeAcademique).order_by(AnneeAcademique.id.desc()).first()
    if annee is None:
        return jsonify(
            {"erreur": "Aucune année académique en base : lancez d'abord le seed."}
        ), 400

    cours = Cours(
        intitule=donnees["intitule"],
        niveau_requis=donnees["niveau_requis"],
        capacite_max=donnees["capacite_max"],
        professeur_id=professeur.id,
        annee_academique_id=annee.id,
    )
    db.session.add(cours)
    db.session.commit()
    return jsonify(_serialize(cours)), 201


@cours_bp.put("/<int:cours_id>")
def modifier_cours(cours_id):
    cours = db.session.get(Cours, cours_id)
    if cours is None:
        return jsonify({"erreur": f"Cours {cours_id} introuvable."}), 404

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    donnees, erreur = valider(CoursSchema(), payload, partial=True)
    if erreur:
        return erreur

    if "professeur_id" in donnees:
        if db.session.get(Professeur, donnees["professeur_id"]) is None:
            return jsonify({"erreur": f"Professeur {donnees['professeur_id']} introuvable."}), 400

    for champ, valeur in donnees.items():
        setattr(cours, champ, valeur)

    db.session.commit()
    return jsonify(_serialize(cours)), 200


@cours_bp.delete("/<int:cours_id>")
def supprimer_cours(cours_id):
    cours = db.session.get(Cours, cours_id)
    if cours is None:
        return jsonify({"erreur": f"Cours {cours_id} introuvable."}), 404

    # Pas de vérification de dépendances : un cours qui a déjà des examens
    # ou des inscriptions peut être supprimé tel quel. À encadrer si votre
    # équipe le juge nécessaire (cf. commentaire dans app/models/cours.py).
    db.session.delete(cours)
    db.session.commit()
    return jsonify({"message": f"Cours {cours_id} supprimé."}), 200

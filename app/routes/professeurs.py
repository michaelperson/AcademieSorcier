"""
CRUD sur Professeur. Validation stricte (jour 4) via ProfesseurSchema —
voir app/schemas.py et app/validation.py.

Sortie typée (bonus) : voir app/dal/dto/professeurs.py::ProfesseurDTO.
"""

from flask import Blueprint, jsonify, request

from app.dal.dto import ProfesseurDTO, vers_dict
from app.extensions import db
from app.dal.models import Professeur
from app.schemas import ProfesseurSchema
from app.validation import valider

professeurs_bp = Blueprint("professeurs", __name__, url_prefix="/professeurs")


def _construire_dto(professeur: Professeur) -> ProfesseurDTO:
    return ProfesseurDTO(
        id=professeur.id,
        nom=professeur.nom,
        matiere_enseignee=professeur.matiere_enseignee,
        anciennete=professeur.anciennete,
    )


def _serialize(professeur: Professeur) -> dict:
    return vers_dict(_construire_dto(professeur))


@professeurs_bp.get("")
def lister_professeurs():
    professeurs = db.session.query(Professeur).order_by(Professeur.nom).all()
    return jsonify([_serialize(p) for p in professeurs]), 200


@professeurs_bp.get("/<int:professeur_id>")
def obtenir_professeur(professeur_id):
    professeur = db.session.get(Professeur, professeur_id)
    if professeur is None:
        return jsonify({"erreur": f"Professeur {professeur_id} introuvable."}), 404
    return jsonify(_serialize(professeur)), 200


@professeurs_bp.post("")
def creer_professeur():
    donnees, erreur = valider(ProfesseurSchema(), request.get_json(silent=True))
    if erreur:
        return erreur

    professeur = Professeur(**donnees)
    db.session.add(professeur)
    db.session.commit()
    return jsonify(_serialize(professeur)), 201


@professeurs_bp.put("/<int:professeur_id>")
def modifier_professeur(professeur_id):
    professeur = db.session.get(Professeur, professeur_id)
    if professeur is None:
        return jsonify({"erreur": f"Professeur {professeur_id} introuvable."}), 404

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    donnees, erreur = valider(ProfesseurSchema(), payload, partial=True)
    if erreur:
        return erreur

    for champ, valeur in donnees.items():
        setattr(professeur, champ, valeur)

    db.session.commit()
    return jsonify(_serialize(professeur)), 200


@professeurs_bp.delete("/<int:professeur_id>")
def supprimer_professeur(professeur_id):
    professeur = db.session.get(Professeur, professeur_id)
    if professeur is None:
        return jsonify({"erreur": f"Professeur {professeur_id} introuvable."}), 404

    # Pas de vérification de dépendances : un professeur qui a encore des
    # cours peut être supprimé tel quel. À encadrer si votre équipe le juge
    # nécessaire.
    db.session.delete(professeur)
    db.session.commit()
    return jsonify({"message": f"Professeur {professeur_id} supprimé."}), 200

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Professeur

professeurs_bp = Blueprint("professeurs", __name__, url_prefix="/professeurs")

CHAMPS_MODIFIABLES = ("nom", "matiere_enseignee", "anciennete")


def _serialize(professeur: Professeur) -> dict:
    return {
        "id": professeur.id,
        "nom": professeur.nom,
        "matiere_enseignee": professeur.matiere_enseignee,
        "anciennete": professeur.anciennete,
    }


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
    payload = request.get_json(silent=True) or {}

    champs_requis = ["nom", "matiere_enseignee", "anciennete"]
    manquants = [c for c in champs_requis if payload.get(c) in (None, "")]
    if manquants:
        return jsonify({"erreur": f"Champ(s) manquant(s) : {', '.join(manquants)}."}), 400

    try:
        anciennete = int(payload["anciennete"])
    except (TypeError, ValueError):
        return jsonify({"erreur": "anciennete doit être un entier."}), 400

    professeur = Professeur(
        nom=payload["nom"],
        matiere_enseignee=payload["matiere_enseignee"],
        anciennete=anciennete,
    )
    db.session.add(professeur)
    db.session.commit()
    return jsonify(_serialize(professeur)), 201


@professeurs_bp.put("/<int:professeur_id>")
def modifier_professeur(professeur_id):
    professeur = db.session.get(Professeur, professeur_id)
    if professeur is None:
        return jsonify({"erreur": f"Professeur {professeur_id} introuvable."}), 404

    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    if "anciennete" in payload:
        try:
            payload["anciennete"] = int(payload["anciennete"])
        except (TypeError, ValueError):
            return jsonify({"erreur": "anciennete doit être un entier."}), 400

    for champ in CHAMPS_MODIFIABLES:
        if champ in payload:
            setattr(professeur, champ, payload[champ])

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

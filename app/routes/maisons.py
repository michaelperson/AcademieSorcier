"""
CRUD sur Maison. Pas de protection par rôle à ce stade (voir README,
section "Où continuer" du jour 1) : le cahier des charges du jour 1 veut
que ces ressources soient testables librement en fin de journée.
`reputation` n'est pas exposé en écriture : ce champ est piloté par la
clôture d'un tournoi (jour 3), pas par un appel API direct.
"""

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Maison

maisons_bp = Blueprint("maisons", __name__, url_prefix="/maisons")

CHAMPS_MODIFIABLES = ("nom", "couleur", "fondateur", "valeurs")


def _serialize(maison: Maison) -> dict:
    return {
        "id": maison.id,
        "nom": maison.nom,
        "couleur": maison.couleur,
        "fondateur": maison.fondateur,
        "valeurs": maison.valeurs,
        "reputation": maison.reputation,
    }


@maisons_bp.get("")
def lister_maisons():
    maisons = db.session.query(Maison).order_by(Maison.nom).all()
    return jsonify([_serialize(m) for m in maisons]), 200


@maisons_bp.get("/<int:maison_id>")
def obtenir_maison(maison_id):
    maison = db.session.get(Maison, maison_id)
    if maison is None:
        return jsonify({"erreur": f"Maison {maison_id} introuvable."}), 404
    return jsonify(_serialize(maison)), 200


@maisons_bp.post("")
def creer_maison():
    payload = request.get_json(silent=True) or {}

    champs_requis = ["nom", "couleur", "fondateur"]
    manquants = [c for c in champs_requis if not payload.get(c)]
    if manquants:
        return jsonify({"erreur": f"Champ(s) manquant(s) : {', '.join(manquants)}."}), 400

    if db.session.query(Maison).filter_by(nom=payload["nom"]).first() is not None:
        return jsonify({"erreur": f"Une maison nommée {payload['nom']!r} existe déjà."}), 400

    maison = Maison(
        nom=payload["nom"],
        couleur=payload["couleur"],
        fondateur=payload["fondateur"],
        valeurs=payload.get("valeurs"),
    )
    db.session.add(maison)
    db.session.commit()
    return jsonify(_serialize(maison)), 201


@maisons_bp.put("/<int:maison_id>")
def modifier_maison(maison_id):
    maison = db.session.get(Maison, maison_id)
    if maison is None:
        return jsonify({"erreur": f"Maison {maison_id} introuvable."}), 404

    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    for champ in CHAMPS_MODIFIABLES:
        if champ in payload:
            setattr(maison, champ, payload[champ])

    db.session.commit()
    return jsonify(_serialize(maison)), 200


@maisons_bp.delete("/<int:maison_id>")
def supprimer_maison(maison_id):
    maison = db.session.get(Maison, maison_id)
    if maison is None:
        return jsonify({"erreur": f"Maison {maison_id} introuvable."}), 404

    # Pas de vérification de dépendances : à ajouter si vous voulez empêcher
    # la suppression d'une maison qui a encore des élèves rattachés.
    db.session.delete(maison)
    db.session.commit()
    return jsonify({"message": f"Maison {maison_id} supprimée."}), 200

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Eleve, Maison
from app.models.enums import StatutEleve

eleves_bp = Blueprint("eleves", __name__, url_prefix="/eleves")

CHAMPS_MODIFIABLES = ("nom", "annee_etude", "maison_id", "familier", "statut")


def _serialize(eleve: Eleve) -> dict:
    return {
        "id": eleve.id,
        "nom": eleve.nom,
        "annee_etude": eleve.annee_etude,
        "maison_id": eleve.maison_id,
        "familier": eleve.familier,
        "statut": eleve.statut.value,
    }


def _valider_annee_etude(payload, obligatoire):
    if "annee_etude" not in payload:
        return None if not obligatoire else "annee_etude est requis."

    try:
        annee = int(payload["annee_etude"])
    except (TypeError, ValueError):
        return "annee_etude doit être un entier."

    if not 1 <= annee <= 7:
        return "annee_etude doit être compris entre 1 et 7."

    payload["annee_etude"] = annee
    return None


def _valider_statut(payload):
    if "statut" not in payload:
        return None
    try:
        payload["statut"] = StatutEleve(payload["statut"])
    except ValueError:
        valeurs = ", ".join(s.value for s in StatutEleve)
        return f"statut invalide : valeurs possibles {valeurs}."
    return None


@eleves_bp.get("")
def lister_eleves():
    eleves = db.session.query(Eleve).order_by(Eleve.nom).all()
    return jsonify([_serialize(e) for e in eleves]), 200


@eleves_bp.get("/<int:eleve_id>")
def obtenir_eleve(eleve_id):
    eleve = db.session.get(Eleve, eleve_id)
    if eleve is None:
        return jsonify({"erreur": f"Élève {eleve_id} introuvable."}), 404
    return jsonify(_serialize(eleve)), 200


@eleves_bp.post("")
def creer_eleve():
    payload = request.get_json(silent=True) or {}

    champs_requis = ["nom", "annee_etude", "maison_id"]
    manquants = [c for c in champs_requis if payload.get(c) in (None, "")]
    if manquants:
        return jsonify({"erreur": f"Champ(s) manquant(s) : {', '.join(manquants)}."}), 400

    erreur = _valider_annee_etude(payload, obligatoire=True)
    if erreur:
        return jsonify({"erreur": erreur}), 400

    try:
        maison_id = int(payload["maison_id"])
    except (TypeError, ValueError):
        return jsonify({"erreur": "maison_id doit être un entier."}), 400

    if db.session.get(Maison, maison_id) is None:
        return jsonify({"erreur": f"Maison {maison_id} introuvable."}), 400

    erreur = _valider_statut(payload)
    if erreur:
        return jsonify({"erreur": erreur}), 400

    eleve = Eleve(
        nom=payload["nom"],
        annee_etude=payload["annee_etude"],
        maison_id=maison_id,
        familier=payload.get("familier"),
        statut=payload.get("statut", StatutEleve.ACTIF),
    )
    db.session.add(eleve)
    db.session.commit()
    return jsonify(_serialize(eleve)), 201


@eleves_bp.put("/<int:eleve_id>")
def modifier_eleve(eleve_id):
    eleve = db.session.get(Eleve, eleve_id)
    if eleve is None:
        return jsonify({"erreur": f"Élève {eleve_id} introuvable."}), 404

    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    erreur = _valider_annee_etude(payload, obligatoire=False)
    if erreur:
        return jsonify({"erreur": erreur}), 400

    erreur = _valider_statut(payload)
    if erreur:
        return jsonify({"erreur": erreur}), 400

    if "maison_id" in payload:
        try:
            payload["maison_id"] = int(payload["maison_id"])
        except (TypeError, ValueError):
            return jsonify({"erreur": "maison_id doit être un entier."}), 400
        if db.session.get(Maison, payload["maison_id"]) is None:
            return jsonify({"erreur": f"Maison {payload['maison_id']} introuvable."}), 400

    for champ in CHAMPS_MODIFIABLES:
        if champ in payload:
            setattr(eleve, champ, payload[champ])

    db.session.commit()
    return jsonify(_serialize(eleve)), 200


@eleves_bp.delete("/<int:eleve_id>")
def supprimer_eleve(eleve_id):
    eleve = db.session.get(Eleve, eleve_id)
    if eleve is None:
        return jsonify({"erreur": f"Élève {eleve_id} introuvable."}), 404

    # Pas de vérification de dépendances (inscriptions, résultats, maîtrises,
    # compte utilisateur lié) : à encadrer si votre équipe le juge nécessaire.
    # Notez que le cahier des charges préfère d'ailleurs l'archivage
    # (statut = diplome) à la suppression pour la fin de cursus (jour 4) —
    # cette suppression brute reste utile pour corriger une erreur de saisie.
    db.session.delete(eleve)
    db.session.commit()
    return jsonify({"message": f"Élève {eleve_id} supprimé."}), 200

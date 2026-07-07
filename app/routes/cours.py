from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import AnneeAcademique, Cours, Professeur

cours_bp = Blueprint("cours", __name__, url_prefix="/cours")

CHAMPS_MODIFIABLES = ("intitule", "niveau_requis", "capacite_max", "professeur_id")


def _serialize(cours: Cours) -> dict:
    return {
        "id": cours.id,
        "intitule": cours.intitule,
        "niveau_requis": cours.niveau_requis,
        "capacite_max": cours.capacite_max,
        "professeur_id": cours.professeur_id,
        "annee_academique_id": cours.annee_academique_id,
    }


def _valider_entiers(payload, champs):
    """Convertit en place les champs listés en int. Retourne un message
    d'erreur (str) au premier champ invalide, ou None si tout est correct.
    """
    for champ in champs:
        if champ not in payload:
            continue
        try:
            payload[champ] = int(payload[champ])
        except (TypeError, ValueError):
            return f"{champ} doit être un entier."
    return None


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
    payload = request.get_json(silent=True) or {}

    champs_requis = ["intitule", "niveau_requis", "capacite_max", "professeur_id"]
    manquants = [c for c in champs_requis if payload.get(c) in (None, "")]
    if manquants:
        return jsonify({"erreur": f"Champ(s) manquant(s) : {', '.join(manquants)}."}), 400

    erreur = _valider_entiers(payload, ["niveau_requis", "capacite_max", "professeur_id"])
    if erreur:
        return jsonify({"erreur": erreur}), 400

    professeur = db.session.get(Professeur, payload["professeur_id"])
    if professeur is None:
        return jsonify({"erreur": f"Professeur {payload['professeur_id']} introuvable."}), 400

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
        intitule=payload["intitule"],
        niveau_requis=payload["niveau_requis"],
        capacite_max=payload["capacite_max"],
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

    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    erreur = _valider_entiers(payload, ["niveau_requis", "capacite_max", "professeur_id"])
    if erreur:
        return jsonify({"erreur": erreur}), 400

    if "professeur_id" in payload:
        if db.session.get(Professeur, payload["professeur_id"]) is None:
            return jsonify({"erreur": f"Professeur {payload['professeur_id']} introuvable."}), 400

    for champ in CHAMPS_MODIFIABLES:
        if champ in payload:
            setattr(cours, champ, payload[champ])

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

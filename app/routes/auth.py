from flask import Blueprint, g, jsonify, request

from app.auth import connexion_requise
from app.extensions import db
from app.dal.models import Utilisateur

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    email = payload.get("email")
    mot_de_passe = payload.get("mot_de_passe")

    if not email or not mot_de_passe:
        return jsonify({"erreur": "email et mot_de_passe sont requis."}), 400

    utilisateur = db.session.query(Utilisateur).filter_by(email=email).one_or_none()

    # Comparaison en clair, comme demandé par le cahier des charges au jour 1.
    # TODO sécurité : à remplacer par une comparaison de hash avant toute
    # mise en situation réelle.
    if utilisateur is None or utilisateur.mot_de_passe != mot_de_passe:
        return jsonify({"erreur": "Email ou mot de passe incorrect."}), 401

    return jsonify(
        {
            "id": utilisateur.id,
            "email": utilisateur.email,
            "role": utilisateur.role.value,
            "eleve_id": utilisateur.eleve_id,
            "professeur_id": utilisateur.professeur_id,
        }
    ), 200


@auth_bp.get("/whoami")
@connexion_requise
def whoami():
    """Endpoint de diagnostic : renvoie l'identité résolue à partir du
    header X-User-Id. Pratique pour vérifier au curl qu'un id donné est
    bien reconnu avant de tester des endpoints plus complexes.
    """
    utilisateur = g.utilisateur_courant
    return jsonify(
        {
            "id": utilisateur.id,
            "email": utilisateur.email,
            "role": utilisateur.role.value,
            "eleve_id": utilisateur.eleve_id,
            "professeur_id": utilisateur.professeur_id,
        }
    ), 200

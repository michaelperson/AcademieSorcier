"""
Blueprint de vérification, sans logique métier : sert uniquement à prouver
que l'application démarre, que la configuration est chargée et que le
client de test fonctionne. Point de départ pour comprendre le pattern
blueprint avant d'écrire les vraies ressources (Maison, Professeur, ...).
"""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify({"status": "ok"}), 200

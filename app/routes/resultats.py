"""
Espace admin du jour 2 : liste filtrable des résultats par cours ou par
examen, moyenne par cours.
"""

from flask import Blueprint, jsonify, request

from app.extensions import db
from app.models import Cours, Examen, Resultat

resultats_bp = Blueprint("resultats", __name__)


def _serialize_resultat(resultat: Resultat) -> dict:
    return {
        "id": resultat.id,
        "eleve_id": resultat.eleve_id,
        "examen_id": resultat.examen_id,
        "cours_id": resultat.examen.cours_id,
        "note": resultat.note,
        "statut": resultat.statut.value if resultat.statut else None,
    }


@resultats_bp.get("/resultats")
def lister_resultats():
    """Filtrable par ?cours_id=... et/ou ?examen_id=..., les deux étant
    combinables. Sans aucun filtre, renvoie tous les résultats.
    """
    query = db.session.query(Resultat).join(Examen, Resultat.examen_id == Examen.id)

    cours_id = request.args.get("cours_id")
    if cours_id is not None:
        try:
            cours_id = int(cours_id)
        except ValueError:
            return jsonify({"erreur": "cours_id doit être un entier."}), 400
        query = query.filter(Examen.cours_id == cours_id)

    examen_id = request.args.get("examen_id")
    if examen_id is not None:
        try:
            examen_id = int(examen_id)
        except ValueError:
            return jsonify({"erreur": "examen_id doit être un entier."}), 400
        query = query.filter(Resultat.examen_id == examen_id)

    resultats = query.all()
    return jsonify([_serialize_resultat(r) for r in resultats]), 200


@resultats_bp.get("/cours/<int:cours_id>/moyenne")
def moyenne_du_cours(cours_id):
    """Moyenne de tous les résultats de tous les examens de ce cours,
    tous élèves confondus — le pendant "vue d'ensemble" de la moyenne par
    élève calculée à la clôture d'un examen.
    """
    if db.session.get(Cours, cours_id) is None:
        return jsonify({"erreur": f"Cours {cours_id} introuvable."}), 404

    resultats = (
        db.session.query(Resultat)
        .join(Examen, Resultat.examen_id == Examen.id)
        .filter(Examen.cours_id == cours_id)
        .all()
    )
    if not resultats:
        return jsonify({"cours_id": cours_id, "moyenne": None, "nombre_resultats": 0}), 200

    moyenne = sum(r.note for r in resultats) / len(resultats)
    return (
        jsonify(
            {"cours_id": cours_id, "moyenne": round(moyenne, 2), "nombre_resultats": len(resultats)}
        ),
        200,
    )

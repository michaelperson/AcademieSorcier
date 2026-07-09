"""
Espace admin du jour 2 : liste filtrable des résultats par cours ou par
examen, moyenne par cours.

Sortie typée (bonus) : voir app/dal/dto/resultats.py::ResultatDetailleDTO —
distincte de ResultatDTO (app/dal/dto/examens.py) parce que ce listing
ajoute cours_id, une information que l'URL ne donne pas déjà ici
(contrairement aux endpoints scopés sous /examens/<id>/...).

Documentation OpenAPI (bonus) : voir app/openapi_generator.py — chaque vue
porte son propre bloc YAML dans sa docstring.
"""

from flask import Blueprint, jsonify, request

from app.dal.dto import ResultatDetailleDTO, vers_dict
from app.extensions import db
from app.dal.models import Cours, Examen, Resultat

resultats_bp = Blueprint("resultats", __name__)


def _construire_dto(resultat: Resultat) -> ResultatDetailleDTO:
    return ResultatDetailleDTO(
        id=resultat.id,
        eleve_id=resultat.eleve_id,
        examen_id=resultat.examen_id,
        cours_id=resultat.examen.cours_id,
        note=resultat.note,
        statut=resultat.statut.value if resultat.statut else None,
    )


def _serialize_resultat(resultat: Resultat) -> dict:
    return vers_dict(_construire_dto(resultat))


@resultats_bp.get("/resultats")
def lister_resultats():
    """Filtrable par ?cours_id=... et/ou ?examen_id=..., les deux étant
    combinables. Sans aucun filtre, renvoie tous les résultats.
    ---
    get:
      tags:
        - Résultats
      summary: Lister les résultats, filtrable par cours et/ou par examen
      parameters:
        - in: query
          name: cours_id
          schema:
            type: integer
        - in: query
          name: examen_id
          schema:
            type: integer
      responses:
        200:
          description: Liste des résultats correspondant aux filtres.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Resultat'
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
    ---
    get:
      tags:
        - Résultats
      summary: Moyenne de tous les résultats du cours
      parameters:
        - in: path
          name: cours_id
          required: true
          schema:
            type: integer
          example: 1
      responses:
        200:
          description: Moyenne calculée.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MoyenneCours'
        404:
          description: Cours introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
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

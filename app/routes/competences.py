"""
Catalogue des compétences magiques (jour 3). Lecture ouverte à tout le
monde (parcourir le catalogue n'a rien de sensible), écriture réservée à
l'admin — le cahier des charges range explicitement "gérer le catalogue
de compétences" du côté espace admin, contrairement au CRUD du jour 1
qui restait volontairement ouvert pour être testé librement.
"""

from flask import Blueprint, jsonify, request

from app.auth import role_requis
from app.extensions import db
from app.models import Competence, Examen
from app.models.enums import RoleUtilisateur, SourceDeblocage
from app.pagination import paginer

competences_bp = Blueprint("competences", __name__)


def _serialize_competence(competence: Competence) -> dict:
    return {
        "id": competence.id,
        "nom": competence.nom,
        "categorie": competence.categorie,
        "description": competence.description,
        "condition_type": competence.condition_type.value,
        "examen_id": competence.examen_id,
        "note_min": competence.note_min,
    }


def _valider_payload_competence(payload, competence_existante=None):
    """Renvoie (donnees, erreur). `erreur` est None si tout est valide.

    Un peu de validation à la main plutôt qu'un attendu jour 4
    (marshmallow/pydantic) : on ne veut pas d'une Competence dont
    condition_type == EXAMEN sans examen_id ni note_min, ni l'inverse
    (un examen_id qui traînerait sur une compétence à condition "tournoi").
    """
    champs_requis = ["nom", "categorie", "description", "condition_type"]
    manquants = [c for c in champs_requis if not payload.get(c)]
    if competence_existante is None and manquants:
        return None, f"Champ(s) manquant(s) : {', '.join(manquants)}."

    donnees = {}
    for champ in ("nom", "categorie", "description"):
        if champ in payload:
            donnees[champ] = payload[champ]

    if "condition_type" in payload:
        try:
            condition_type = SourceDeblocage(payload["condition_type"])
        except ValueError:
            return None, "condition_type doit être 'examen' ou 'tournoi'."
        donnees["condition_type"] = condition_type
    else:
        condition_type = competence_existante.condition_type if competence_existante else None

    if condition_type == SourceDeblocage.EXAMEN:
        examen_id = payload.get("examen_id", competence_existante.examen_id if competence_existante else None)
        note_min = payload.get("note_min", competence_existante.note_min if competence_existante else None)
        if examen_id is None or note_min is None:
            return None, "condition_type 'examen' exige examen_id et note_min."
        if db.session.get(Examen, examen_id) is None:
            return None, f"Examen {examen_id} introuvable."
        try:
            note_min = float(note_min)
        except (TypeError, ValueError):
            return None, "note_min doit être un nombre."
        donnees["examen_id"] = examen_id
        donnees["note_min"] = note_min
    elif condition_type == SourceDeblocage.TOURNOI:
        # Une compétence à condition "tournoi" n'est pas liée à un examen
        # précis : on force ces deux colonnes à rester vides, pour éviter
        # une combinaison incohérente (condition tournoi + examen_id posé).
        donnees["examen_id"] = None
        donnees["note_min"] = None

    return donnees, None


@competences_bp.get("/competences")
def lister_competences():
    """Filtrable par ?categorie=..., paginé (?page=&par_page=)."""
    requete = db.session.query(Competence).order_by(Competence.nom)

    categorie = request.args.get("categorie")
    if categorie:
        requete = requete.filter(Competence.categorie == categorie)

    return jsonify(paginer(requete, request, _serialize_competence)), 200


@competences_bp.post("/competences")
@role_requis(RoleUtilisateur.ADMIN)
def creer_competence():
    payload = request.get_json(silent=True) or {}
    donnees, erreur = _valider_payload_competence(payload)
    if erreur:
        return jsonify({"erreur": erreur}), 400

    competence = Competence(**donnees)
    db.session.add(competence)
    db.session.commit()
    return jsonify(_serialize_competence(competence)), 201


@competences_bp.get("/competences/<int:competence_id>")
def obtenir_competence(competence_id):
    competence = db.session.get(Competence, competence_id)
    if competence is None:
        return jsonify({"erreur": f"Compétence {competence_id} introuvable."}), 404
    return jsonify(_serialize_competence(competence)), 200


@competences_bp.put("/competences/<int:competence_id>")
@role_requis(RoleUtilisateur.ADMIN)
def modifier_competence(competence_id):
    competence = db.session.get(Competence, competence_id)
    if competence is None:
        return jsonify({"erreur": f"Compétence {competence_id} introuvable."}), 404

    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    donnees, erreur = _valider_payload_competence(payload, competence_existante=competence)
    if erreur:
        return jsonify({"erreur": erreur}), 400

    for champ, valeur in donnees.items():
        setattr(competence, champ, valeur)

    db.session.commit()
    return jsonify(_serialize_competence(competence)), 200


@competences_bp.delete("/competences/<int:competence_id>")
@role_requis(RoleUtilisateur.ADMIN)
def supprimer_competence(competence_id):
    competence = db.session.get(Competence, competence_id)
    if competence is None:
        return jsonify({"erreur": f"Compétence {competence_id} introuvable."}), 404

    db.session.delete(competence)
    db.session.commit()
    return jsonify({"message": f"Compétence {competence_id} supprimée."}), 200

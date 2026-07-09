"""
Catalogue des compétences magiques (jour 3). Lecture ouverte à tout le
monde (parcourir le catalogue n'a rien de sensible), écriture réservée à
l'admin — le cahier des charges range explicitement "gérer le catalogue
de compétences" du côté espace admin, contrairement au CRUD du jour 1
qui restait volontairement ouvert pour être testé librement.

Sortie typée (bonus) : voir app/dal/dto/competences.py::CompetenceDTO.

Documentation OpenAPI (bonus) : voir app/openapi_generator.py — chaque vue
porte son propre bloc YAML dans sa docstring.
"""

from flask import Blueprint, jsonify, request

from app.auth import role_requis
from app.dal.dto import CompetenceDTO, vers_dict
from app.extensions import db
from app.dal.models import Competence, Examen
from app.dal.models.enums import RoleUtilisateur, SourceDeblocage
from app.pagination import paginer
from app.schemas import CompetenceModificationSchema, CompetenceSchema
from app.validation import valider

competences_bp = Blueprint("competences", __name__)


def _construire_dto(competence: Competence) -> CompetenceDTO:
    return CompetenceDTO(
        id=competence.id,
        nom=competence.nom,
        categorie=competence.categorie,
        description=competence.description,
        condition_type=competence.condition_type.value,
        examen_id=competence.examen_id,
        note_min=competence.note_min,
    )


def _serialize_competence(competence: Competence) -> dict:
    return vers_dict(_construire_dto(competence))


def _verifier_coherence_condition(donnees, competence_existante=None):
    """CompetenceSchema (jour 4) valide déjà les types et bornes de base.
    Ce qui reste à vérifier ici, à la main : la cohérence entre
    condition_type et (examen_id, note_min), qui dépend de l'existence en
    base de l'examen référencé et, pour un PUT partiel, de l'état déjà
    enregistré sur la ligne (ex. changer uniquement la description d'une
    compétence à condition "examen" ne doit pas exiger de renvoyer
    examen_id/note_min à chaque fois).

    Mute `donnees` en place (force examen_id/note_min à None si la
    condition est "tournoi"). Retourne un message d'erreur (str), ou None
    si tout est cohérent.
    """
    condition_type = donnees.get("condition_type")
    if condition_type is None and competence_existante is not None:
        condition_type = competence_existante.condition_type.value

    if condition_type == SourceDeblocage.EXAMEN.value:
        examen_id = donnees.get(
            "examen_id", competence_existante.examen_id if competence_existante else None
        )
        note_min = donnees.get(
            "note_min", competence_existante.note_min if competence_existante else None
        )
        if examen_id is None or note_min is None:
            return "condition_type 'examen' exige examen_id et note_min."
        if db.session.get(Examen, examen_id) is None:
            return f"Examen {examen_id} introuvable."
        donnees["examen_id"] = examen_id
        donnees["note_min"] = note_min
    elif condition_type == SourceDeblocage.TOURNOI.value:
        # Une compétence à condition "tournoi" n'est pas liée à un examen
        # précis : on force ces deux colonnes à rester vides, pour éviter
        # une combinaison incohérente (condition tournoi + examen_id posé).
        donnees["examen_id"] = None
        donnees["note_min"] = None

    return None


@competences_bp.get("/competences")
def lister_competences():
    """Filtrable par ?categorie=..., paginé (?page=&par_page=).
    ---
    get:
      tags:
        - Compétences
      summary: Lister le catalogue de compétences
      description: Filtrable par ?categorie=..., paginé (?page=&par_page=).
      parameters:
        - in: query
          name: categorie
          schema:
            type: string
        - in: query
          name: page
          schema:
            type: integer
            default: 1
        - in: query
          name: par_page
          schema:
            type: integer
            default: 20
      responses:
        200:
          description: Page de compétences.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/CompetencesPage'
    """
    requete = db.session.query(Competence).order_by(Competence.nom)

    categorie = request.args.get("categorie")
    if categorie:
        requete = requete.filter(Competence.categorie == categorie)

    return jsonify(paginer(requete, request, _serialize_competence)), 200


@competences_bp.post("/competences")
@role_requis(RoleUtilisateur.ADMIN)
def creer_competence():
    """Ajouter une compétence au catalogue (admin).
    ---
    post:
      tags:
        - Compétences
      summary: Ajouter une compétence au catalogue (admin)
      security:
        - XUserId: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompetenceEcriture'
      responses:
        201:
          description: Compétence créée.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Competence'
        400:
          description: Payload invalide, ou condition_type incohérent avec examen_id/note_min.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErreurValidation'
        401:
          description: Header X-User-Id manquant ou invalide.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
        403:
          description: Réservé à l'admin.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    donnees, erreur = valider(CompetenceSchema(), request.get_json(silent=True))
    if erreur:
        return erreur

    erreur_coherence = _verifier_coherence_condition(donnees)
    if erreur_coherence:
        return jsonify({"erreur": erreur_coherence}), 400

    donnees["condition_type"] = SourceDeblocage(donnees["condition_type"])

    competence = Competence(**donnees)
    db.session.add(competence)
    db.session.commit()
    return jsonify(_serialize_competence(competence)), 201


@competences_bp.get("/competences/<int:competence_id>")
def obtenir_competence(competence_id):
    """Obtenir une compétence par id.
    ---
    get:
      tags:
        - Compétences
      summary: Obtenir une compétence
      parameters:
        - in: path
          name: competence_id
          required: true
          schema:
            type: integer
          example: 1
      responses:
        200:
          description: Compétence trouvée.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Competence'
        404:
          description: Compétence introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    competence = db.session.get(Competence, competence_id)
    if competence is None:
        return jsonify({"erreur": f"Compétence {competence_id} introuvable."}), 404
    return jsonify(_serialize_competence(competence)), 200


@competences_bp.put("/competences/<int:competence_id>")
@role_requis(RoleUtilisateur.ADMIN)
def modifier_competence(competence_id):
    """Modifier une compétence (admin).
    ---
    put:
      tags:
        - Compétences
      summary: Modifier une compétence (admin)
      security:
        - XUserId: []
      parameters:
        - in: path
          name: competence_id
          required: true
          schema:
            type: integer
          example: 1
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CompetenceEcriture'
      responses:
        200:
          description: Compétence modifiée.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Competence'
        400:
          description: Payload invalide.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErreurValidation'
        403:
          description: Réservé à l'admin.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
        404:
          description: Compétence introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    competence = db.session.get(Competence, competence_id)
    if competence is None:
        return jsonify({"erreur": f"Compétence {competence_id} introuvable."}), 404

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    donnees, erreur = valider(CompetenceModificationSchema(), payload, partial=True)
    if erreur:
        return erreur

    erreur_coherence = _verifier_coherence_condition(donnees, competence_existante=competence)
    if erreur_coherence:
        return jsonify({"erreur": erreur_coherence}), 400

    if "condition_type" in donnees:
        donnees["condition_type"] = SourceDeblocage(donnees["condition_type"])

    for champ, valeur in donnees.items():
        setattr(competence, champ, valeur)

    db.session.commit()
    return jsonify(_serialize_competence(competence)), 200


@competences_bp.delete("/competences/<int:competence_id>")
@role_requis(RoleUtilisateur.ADMIN)
def supprimer_competence(competence_id):
    """Supprimer une compétence (admin).
    ---
    delete:
      tags:
        - Compétences
      summary: Supprimer une compétence (admin)
      security:
        - XUserId: []
      parameters:
        - in: path
          name: competence_id
          required: true
          schema:
            type: integer
          example: 1
      responses:
        200:
          description: Compétence supprimée.
        403:
          description: Réservé à l'admin.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
        404:
          description: Compétence introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    competence = db.session.get(Competence, competence_id)
    if competence is None:
        return jsonify({"erreur": f"Compétence {competence_id} introuvable."}), 404

    db.session.delete(competence)
    db.session.commit()
    return jsonify({"message": f"Compétence {competence_id} supprimée."}), 200

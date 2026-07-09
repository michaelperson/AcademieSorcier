"""
CRUD sur Professeur. Validation stricte (jour 4) via ProfesseurSchema —
voir app/schemas.py et app/validation.py.

Sortie typée (bonus) : voir app/dal/dto/professeurs.py::ProfesseurDTO.

Documentation OpenAPI (bonus) : voir app/openapi_generator.py — chaque vue
porte son propre bloc YAML dans sa docstring.
"""

from flask import Blueprint, jsonify, request

from app.dal.dto import ProfesseurDTO, vers_dict
from app.extensions import db
from app.dal.models import Professeur
from app.schemas import ProfesseurSchema
from app.validation import valider

professeurs_bp = Blueprint("professeurs", __name__, url_prefix="/professeurs")


def _construire_dto(professeur: Professeur) -> ProfesseurDTO:
    return ProfesseurDTO(
        id=professeur.id,
        nom=professeur.nom,
        matiere_enseignee=professeur.matiere_enseignee,
        anciennete=professeur.anciennete,
    )


def _serialize(professeur: Professeur) -> dict:
    return vers_dict(_construire_dto(professeur))


@professeurs_bp.get("")
def lister_professeurs():
    """Liste tous les professeurs.
    ---
    get:
      tags:
        - Professeurs
      summary: Lister les professeurs
      responses:
        200:
          description: Liste des professeurs.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Professeur'
    """
    professeurs = db.session.query(Professeur).order_by(Professeur.nom).all()
    return jsonify([_serialize(p) for p in professeurs]), 200


@professeurs_bp.get("/<int:professeur_id>")
def obtenir_professeur(professeur_id):
    """Obtenir un professeur par id.
    ---
    get:
      tags:
        - Professeurs
      summary: Obtenir un professeur par id
      parameters:
        - in: path
          name: professeur_id
          required: true
          schema:
            type: integer
          example: 1
      responses:
        200:
          description: Professeur trouvé.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Professeur'
        404:
          description: Professeur introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    professeur = db.session.get(Professeur, professeur_id)
    if professeur is None:
        return jsonify({"erreur": f"Professeur {professeur_id} introuvable."}), 404
    return jsonify(_serialize(professeur)), 200


@professeurs_bp.post("")
def creer_professeur():
    """Créer un professeur.
    ---
    post:
      tags:
        - Professeurs
      summary: Créer un professeur
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProfesseurEcriture'
      responses:
        201:
          description: Professeur créé.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Professeur'
        400:
          description: Payload invalide (champ manquant ou type incorrect).
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErreurValidation'
    """
    donnees, erreur = valider(ProfesseurSchema(), request.get_json(silent=True))
    if erreur:
        return erreur

    professeur = Professeur(**donnees)
    db.session.add(professeur)
    db.session.commit()
    return jsonify(_serialize(professeur)), 201


@professeurs_bp.put("/<int:professeur_id>")
def modifier_professeur(professeur_id):
    """Modifier un professeur.
    ---
    put:
      tags:
        - Professeurs
      summary: Modifier un professeur
      parameters:
        - in: path
          name: professeur_id
          required: true
          schema:
            type: integer
          example: 1
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProfesseurEcriture'
      responses:
        200:
          description: Professeur modifié.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Professeur'
        400:
          description: Payload invalide.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErreurValidation'
        404:
          description: Professeur introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    professeur = db.session.get(Professeur, professeur_id)
    if professeur is None:
        return jsonify({"erreur": f"Professeur {professeur_id} introuvable."}), 404

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    donnees, erreur = valider(ProfesseurSchema(), payload, partial=True)
    if erreur:
        return erreur

    for champ, valeur in donnees.items():
        setattr(professeur, champ, valeur)

    db.session.commit()
    return jsonify(_serialize(professeur)), 200


@professeurs_bp.delete("/<int:professeur_id>")
def supprimer_professeur(professeur_id):
    """Supprimer un professeur.
    ---
    delete:
      tags:
        - Professeurs
      summary: Supprimer un professeur
      parameters:
        - in: path
          name: professeur_id
          required: true
          schema:
            type: integer
          example: 1
      responses:
        200:
          description: Professeur supprimé.
        404:
          description: Professeur introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    professeur = db.session.get(Professeur, professeur_id)
    if professeur is None:
        return jsonify({"erreur": f"Professeur {professeur_id} introuvable."}), 404

    # Pas de vérification de dépendances : un professeur qui a encore des
    # cours peut être supprimé tel quel. À encadrer si votre équipe le juge
    # nécessaire.
    db.session.delete(professeur)
    db.session.commit()
    return jsonify({"message": f"Professeur {professeur_id} supprimé."}), 200

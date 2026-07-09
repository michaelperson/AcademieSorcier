"""
CRUD sur Maison. Pas de protection par rôle à ce stade (voir README,
section "Où continuer" du jour 1) : le cahier des charges du jour 1 veut
que ces ressources soient testables librement en fin de journée.
`reputation` n'est pas exposé en écriture : ce champ est piloté par la
clôture d'un tournoi (jour 3), pas par un appel API direct.

Validation stricte (jour 4) : les champs sont vérifiés par MaisonSchema
(app/schemas.py) avant toute écriture — voir app/validation.py pour le
format de réponse en cas de payload invalide.

Sortie typée (bonus) : _construire_dto donne la forme exacte de la
réponse (MaisonDTO, app/dal/dto/) ; _serialize la convertit en dict pour
jsonify(). Le JSON produit ne change pas, seul le chemin pour l'obtenir
passe maintenant par un type plutôt qu'un dict assemblé à la main.

Documentation OpenAPI (bonus) : chaque vue ci-dessous porte son propre
bloc YAML dans sa docstring (convention apispec) — voir
app/openapi_generator.py, qui les rassemble en une spec unique sans
qu'il faille les maintenir à part.
"""

from flask import Blueprint, jsonify, request

from app.dal.dto import MaisonDTO, vers_dict
from app.extensions import db
from app.dal.models import Maison
from app.schemas import MaisonSchema
from app.validation import valider

maisons_bp = Blueprint("maisons", __name__, url_prefix="/maisons")


def _construire_dto(maison: Maison) -> MaisonDTO:
    return MaisonDTO(
        id=maison.id,
        nom=maison.nom,
        couleur=maison.couleur,
        fondateur=maison.fondateur,
        valeurs=maison.valeurs,
        reputation=maison.reputation,
    )


def _serialize(maison: Maison) -> dict:
    return vers_dict(_construire_dto(maison))


@maisons_bp.get("")
def lister_maisons():
    """Liste toutes les maisons.
    ---
    get:
      tags:
        - Maisons
      summary: Lister les maisons
      responses:
        200:
          description: Liste des maisons.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Maison'
    """
    maisons = db.session.query(Maison).order_by(Maison.nom).all()
    return jsonify([_serialize(m) for m in maisons]), 200


@maisons_bp.get("/<int:maison_id>")
def obtenir_maison(maison_id):
    """Obtenir une maison par id.
    ---
    get:
      tags:
        - Maisons
      summary: Obtenir une maison par id
      parameters:
        - in: path
          name: maison_id
          required: true
          schema:
            type: integer
          example: 1
      responses:
        200:
          description: Maison trouvée.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Maison'
        404:
          description: Maison introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    maison = db.session.get(Maison, maison_id)
    if maison is None:
        return jsonify({"erreur": f"Maison {maison_id} introuvable."}), 404
    return jsonify(_serialize(maison)), 200


@maisons_bp.post("")
def creer_maison():
    """Créer une maison.
    ---
    post:
      tags:
        - Maisons
      summary: Créer une maison
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MaisonEcriture'
      responses:
        201:
          description: Maison créée.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Maison'
        400:
          description: Payload invalide (champ manquant, type incorrect, ou nom déjà pris).
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErreurValidation'
    """
    donnees, erreur = valider(MaisonSchema(), request.get_json(silent=True))
    if erreur:
        return erreur

    if db.session.query(Maison).filter_by(nom=donnees["nom"]).first() is not None:
        return jsonify({"erreur": f"Une maison nommée {donnees['nom']!r} existe déjà."}), 400

    maison = Maison(**donnees)
    db.session.add(maison)
    db.session.commit()
    return jsonify(_serialize(maison)), 201


@maisons_bp.put("/<int:maison_id>")
def modifier_maison(maison_id):
    """Modifier une maison.
    ---
    put:
      tags:
        - Maisons
      summary: Modifier une maison
      parameters:
        - in: path
          name: maison_id
          required: true
          schema:
            type: integer
          example: 1
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MaisonEcriture'
      responses:
        200:
          description: Maison modifiée.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Maison'
        400:
          description: Payload invalide.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErreurValidation'
        404:
          description: Maison introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    maison = db.session.get(Maison, maison_id)
    if maison is None:
        return jsonify({"erreur": f"Maison {maison_id} introuvable."}), 404

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    donnees, erreur = valider(MaisonSchema(), payload, partial=True)
    if erreur:
        return erreur

    for champ, valeur in donnees.items():
        setattr(maison, champ, valeur)

    db.session.commit()
    return jsonify(_serialize(maison)), 200


@maisons_bp.delete("/<int:maison_id>")
def supprimer_maison(maison_id):
    """Supprimer une maison.
    ---
    delete:
      tags:
        - Maisons
      summary: Supprimer une maison
      parameters:
        - in: path
          name: maison_id
          required: true
          schema:
            type: integer
          example: 1
      responses:
        200:
          description: Maison supprimée.
        404:
          description: Maison introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    maison = db.session.get(Maison, maison_id)
    if maison is None:
        return jsonify({"erreur": f"Maison {maison_id} introuvable."}), 404

    # Pas de vérification de dépendances : à ajouter si vous voulez empêcher
    # la suppression d'une maison qui a encore des élèves rattachés.
    db.session.delete(maison)
    db.session.commit()
    return jsonify({"message": f"Maison {maison_id} supprimée."}), 200

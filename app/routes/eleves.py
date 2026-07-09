"""
CRUD sur Élève. Validation stricte (jour 4) via EleveSchema : bornes sur
annee_etude (1-7), valeurs autorisées pour statut. L'existence de la
maison référencée reste vérifiée ici, après le schéma.

Sortie typée (bonus) : voir app/dal/dto/eleves.py::EleveDTO.

Documentation OpenAPI (bonus) : voir app/openapi_generator.py — chaque vue
porte son propre bloc YAML dans sa docstring.
"""

from flask import Blueprint, jsonify, request

from app.dal.dto import EleveDTO, vers_dict
from app.extensions import db
from app.dal.models import Eleve, Maison
from app.dal.models.enums import StatutEleve
from app.schemas import EleveSchema
from app.validation import valider

eleves_bp = Blueprint("eleves", __name__, url_prefix="/eleves")


def _construire_dto(eleve: Eleve) -> EleveDTO:
    return EleveDTO(
        id=eleve.id,
        nom=eleve.nom,
        annee_etude=eleve.annee_etude,
        maison_id=eleve.maison_id,
        familier=eleve.familier,
        statut=eleve.statut.value,
    )


def _serialize(eleve: Eleve) -> dict:
    return vers_dict(_construire_dto(eleve))


@eleves_bp.get("")
def lister_eleves():
    """Liste tous les élèves.
    ---
    get:
      tags:
        - Eleves
      summary: Lister les élèves
      responses:
        200:
          description: Liste des élèves.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Eleve'
    """
    eleves = db.session.query(Eleve).order_by(Eleve.nom).all()
    return jsonify([_serialize(e) for e in eleves]), 200


@eleves_bp.get("/<int:eleve_id>")
def obtenir_eleve(eleve_id):
    """Obtenir un élève par id.
    ---
    get:
      tags:
        - Eleves
      summary: Obtenir un élève par id
      parameters:
        - in: path
          name: eleve_id
          required: true
          schema:
            type: integer
          example: 1
      responses:
        200:
          description: Élève trouvé.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Eleve'
        404:
          description: Élève introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    eleve = db.session.get(Eleve, eleve_id)
    if eleve is None:
        return jsonify({"erreur": f"Élève {eleve_id} introuvable."}), 404
    return jsonify(_serialize(eleve)), 200


@eleves_bp.post("")
def creer_eleve():
    """Créer un élève.
    ---
    post:
      tags:
        - Eleves
      summary: Créer un élève
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EleveEcriture'
      responses:
        201:
          description: Élève créé.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Eleve'
        400:
          description: Payload invalide, ou maison introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErreurValidation'
    """
    donnees, erreur = valider(EleveSchema(), request.get_json(silent=True))
    if erreur:
        return erreur

    if db.session.get(Maison, donnees["maison_id"]) is None:
        return jsonify({"erreur": f"Maison {donnees['maison_id']} introuvable."}), 400

    if "statut" in donnees:
        donnees["statut"] = StatutEleve(donnees["statut"])

    eleve = Eleve(
        nom=donnees["nom"],
        annee_etude=donnees["annee_etude"],
        maison_id=donnees["maison_id"],
        familier=donnees.get("familier"),
        statut=donnees.get("statut", StatutEleve.ACTIF),
    )
    db.session.add(eleve)
    db.session.commit()
    return jsonify(_serialize(eleve)), 201


@eleves_bp.put("/<int:eleve_id>")
def modifier_eleve(eleve_id):
    """Modifier un élève.
    ---
    put:
      tags:
        - Eleves
      summary: Modifier un élève
      parameters:
        - in: path
          name: eleve_id
          required: true
          schema:
            type: integer
          example: 1
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/EleveEcriture'
      responses:
        200:
          description: Élève modifié.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Eleve'
        400:
          description: Payload invalide, ou maison introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErreurValidation'
        404:
          description: Élève introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    eleve = db.session.get(Eleve, eleve_id)
    if eleve is None:
        return jsonify({"erreur": f"Élève {eleve_id} introuvable."}), 404

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    donnees, erreur = valider(EleveSchema(), payload, partial=True)
    if erreur:
        return erreur

    if "maison_id" in donnees:
        if db.session.get(Maison, donnees["maison_id"]) is None:
            return jsonify({"erreur": f"Maison {donnees['maison_id']} introuvable."}), 400

    if "statut" in donnees:
        donnees["statut"] = StatutEleve(donnees["statut"])

    for champ, valeur in donnees.items():
        setattr(eleve, champ, valeur)

    db.session.commit()
    return jsonify(_serialize(eleve)), 200


@eleves_bp.delete("/<int:eleve_id>")
def supprimer_eleve(eleve_id):
    """Supprimer un élève.
    ---
    delete:
      tags:
        - Eleves
      summary: Supprimer un élève
      parameters:
        - in: path
          name: eleve_id
          required: true
          schema:
            type: integer
          example: 1
      responses:
        200:
          description: Élève supprimé.
        404:
          description: Élève introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
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

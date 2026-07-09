"""
Inscrire un élève à un cours, et lister les élèves d'un cours — ce second
endpoint est délibérément celui utilisé pour la chasse au N+1 du jour 2
(voir PERFORMANCE.md) : on y accède à `eleve.maison.nom` pour chaque
élève d'une liste, exactement le scénario décrit par le cahier des charges.

Validation stricte (jour 4) via InscriptionSchema pour eleve_id.

Sortie typée (bonus) : voir app/dal/dto/inscriptions.py::InscriptionDTO et
EleveDuCoursDTO.
"""

from datetime import date

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from app.dal.dto import EleveDuCoursDTO, InscriptionDTO, vers_dict
from app.extensions import db
from app.dal.models import Cours, Eleve, Inscription
from app.dal.models.enums import StatutInscription
from app.schemas import InscriptionSchema
from app.validation import valider

inscriptions_bp = Blueprint("inscriptions", __name__)

# Statuts qui comptent encore comme une place occupée dans le cours.
# Un élève qui a abandonné libère sa place pour quelqu'un d'autre.
STATUTS_OCCUPANT_UNE_PLACE = (
    StatutInscription.INSCRIT,
    StatutInscription.EN_COURS,
    StatutInscription.VALIDE,
)


def _construire_dto(inscription: Inscription) -> InscriptionDTO:
    return InscriptionDTO(
        id=inscription.id,
        eleve_id=inscription.eleve_id,
        cours_id=inscription.cours_id,
        date_inscription=inscription.date_inscription.isoformat(),
        statut=inscription.statut.value,
    )


def _serialize_inscription(inscription: Inscription) -> dict:
    return vers_dict(_construire_dto(inscription))


@inscriptions_bp.post("/cours/<int:cours_id>/inscriptions")
def inscrire_eleve(cours_id):
    cours = db.session.get(Cours, cours_id)
    if cours is None:
        return jsonify({"erreur": f"Cours {cours_id} introuvable."}), 404

    donnees, erreur = valider(InscriptionSchema(), request.get_json(silent=True))
    if erreur:
        return erreur
    eleve_id = donnees["eleve_id"]

    eleve = db.session.get(Eleve, eleve_id)
    if eleve is None:
        return jsonify({"erreur": f"Élève {eleve_id} introuvable."}), 400

    deja_inscrit = (
        db.session.query(Inscription)
        .filter_by(eleve_id=eleve_id, cours_id=cours_id)
        .one_or_none()
    )
    if deja_inscrit is not None:
        return jsonify({"erreur": "Cet élève est déjà inscrit à ce cours."}), 400

    places_occupees = (
        db.session.query(Inscription)
        .filter(
            Inscription.cours_id == cours_id,
            Inscription.statut.in_(STATUTS_OCCUPANT_UNE_PLACE),
        )
        .count()
    )
    if places_occupees >= cours.capacite_max:
        return jsonify({"erreur": f"Le cours {cours.intitule!r} est complet."}), 400

    inscription = Inscription(
        eleve_id=eleve_id,
        cours_id=cours_id,
        date_inscription=date.today(),
        statut=StatutInscription.INSCRIT,
    )
    db.session.add(inscription)
    db.session.commit()
    return jsonify(_serialize_inscription(inscription)), 201


@inscriptions_bp.get("/cours/<int:cours_id>/eleves")
def lister_eleves_du_cours(cours_id):
    """Liste les élèves inscrits à un cours, avec le nom de leur maison.

    Chargement paresseux par défaut (`eleve` puis `eleve.maison` sont
    accédés dans la boucle ci-dessous, une requête par relation et par
    élève) : c'est le scénario N+1 documenté dans PERFORMANCE.md.
    `?eager=true` active `joinedload` pour tout charger en une requête.
    """
    cours = db.session.get(Cours, cours_id)
    if cours is None:
        return jsonify({"erreur": f"Cours {cours_id} introuvable."}), 404

    eager = request.args.get("eager", "false").lower() == "true"

    query = db.session.query(Inscription).filter_by(cours_id=cours_id)
    if eager:
        query = query.options(joinedload(Inscription.eleve).joinedload(Eleve.maison))
    inscriptions = query.all()

    resultat = []
    for inscription in inscriptions:
        eleve = inscription.eleve  # requête lazy #1 par élève si eager=false
        resultat.append(
            EleveDuCoursDTO(
                eleve_id=eleve.id,
                nom=eleve.nom,
                maison=eleve.maison.nom,  # requête lazy #2 si eager=false
                statut_inscription=inscription.statut.value,
            )
        )
    return jsonify([vers_dict(r) for r in resultat]), 200

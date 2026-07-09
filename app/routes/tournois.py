"""
Tournois et duels (jour 3), plus la clôture de tournoi : l'autre endpoint
métier du jour, à côté de l'évaluation des compétences après un examen
(voir app/routes/examens.py::evaluer_competences).

Créer un tournoi, enregistrer un duel et clôturer le tournoi sont des
actions d'admin (le cahier des charges les range explicitement du côté
espace admin) ; consulter les tournois et leurs duels reste ouvert à
tous, dans le même esprit que le catalogue de compétences.

Validation stricte (jour 4) via TournoiSchema et DuelSchema — cette
dernière vérifie aussi, au niveau du schéma, que les deux participants
sont différents et que le vainqueur est l'un des deux (voir
app/schemas.py::DuelSchema._verifier_participants).

Sortie typée (bonus) : voir app/dal/dto/tournois.py::TournoiDTO, DuelDTO,
DuelDetailleDTO et ClotureTournoiDTO.
"""

from collections import Counter
from datetime import date, datetime

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from app.auth import role_requis
from app.dal.dto import (
    ClotureTournoiDTO,
    DuelDetailleDTO,
    DuelDTO,
    EleveMinimalDTO,
    TournoiDTO,
    vers_dict,
)
from app.extensions import db
from app.dal.models import Competence, Duel, Eleve, Maitrise, Tournoi
from app.dal.models.enums import RoleUtilisateur, SourceDeblocage
from app.pagination import paginer
from app.schemas import DuelSchema, TournoiSchema
from app.validation import valider

tournois_bp = Blueprint("tournois", __name__)

# Valeur fixe faute de mieux : le cahier des charges demande d'"ajouter un
# score de réputation" sans en préciser le montant. Un seul point d'entrée
# (cette constante) si l'équipe veut l'ajuster ou le faire varier plus tard
# (ex. selon le nombre de duels gagnés).
POINTS_REPUTATION_VICTOIRE_TOURNOI = 10


def _construire_dto_tournoi(tournoi: Tournoi) -> TournoiDTO:
    return TournoiDTO(
        id=tournoi.id,
        nom=tournoi.nom,
        annee=tournoi.annee,
        maison_organisatrice_id=tournoi.maison_organisatrice_id,
        vainqueur_eleve_id=tournoi.vainqueur_eleve_id,
        cloture_le=tournoi.cloture_le.isoformat() if tournoi.cloture_le else None,
    )


def _serialize_tournoi(tournoi: Tournoi) -> dict:
    return vers_dict(_construire_dto_tournoi(tournoi))


def _construire_dto_duel(duel: Duel) -> DuelDTO:
    return DuelDTO(
        id=duel.id,
        tournoi_id=duel.tournoi_id,
        eleve_1_id=duel.eleve_1_id,
        eleve_2_id=duel.eleve_2_id,
        vainqueur_id=duel.vainqueur_id,
    )


def _serialize_duel(duel: Duel) -> dict:
    return vers_dict(_construire_dto_duel(duel))


@tournois_bp.get("/tournois")
def lister_tournois():
    """Filtrable par ?annee=..., paginé (?page=&par_page=)."""
    requete = db.session.query(Tournoi).order_by(Tournoi.annee.desc(), Tournoi.nom)

    annee = request.args.get("annee")
    if annee:
        try:
            annee = int(annee)
        except ValueError:
            return jsonify({"erreur": "annee doit être un entier."}), 400
        requete = requete.filter(Tournoi.annee == annee)

    return jsonify(paginer(requete, request, _serialize_tournoi)), 200


@tournois_bp.post("/tournois")
@role_requis(RoleUtilisateur.ADMIN)
def creer_tournoi():
    donnees, erreur = valider(TournoiSchema(), request.get_json(silent=True))
    if erreur:
        return erreur

    tournoi = Tournoi(**donnees)
    db.session.add(tournoi)
    db.session.commit()
    return jsonify(_serialize_tournoi(tournoi)), 201


@tournois_bp.get("/tournois/<int:tournoi_id>")
def obtenir_tournoi(tournoi_id):
    tournoi = db.session.get(Tournoi, tournoi_id)
    if tournoi is None:
        return jsonify({"erreur": f"Tournoi {tournoi_id} introuvable."}), 404
    return jsonify(_serialize_tournoi(tournoi)), 200


@tournois_bp.get("/tournois/<int:tournoi_id>/duels")
def lister_duels(tournoi_id):
    """joinedload sur les trois relations Eleve : lister les duels d'un
    tournoi accède presque toujours au nom des participants, donc autant
    éviter le N+1 dès l'écriture plutôt que d'attendre de le mesurer comme
    au jour 2 (voir PERFORMANCE.md pour la démonstration complète).
    """
    if db.session.get(Tournoi, tournoi_id) is None:
        return jsonify({"erreur": f"Tournoi {tournoi_id} introuvable."}), 404

    duels = (
        db.session.query(Duel)
        .filter_by(tournoi_id=tournoi_id)
        .options(
            joinedload(Duel.eleve_1),
            joinedload(Duel.eleve_2),
            joinedload(Duel.vainqueur),
        )
        .all()
    )
    resultat = [
        DuelDetailleDTO(
            id=d.id,
            eleve_1=EleveMinimalDTO(id=d.eleve_1_id, nom=d.eleve_1.nom),
            eleve_2=EleveMinimalDTO(id=d.eleve_2_id, nom=d.eleve_2.nom),
            vainqueur=EleveMinimalDTO(id=d.vainqueur_id, nom=d.vainqueur.nom) if d.vainqueur else None,
        )
        for d in duels
    ]
    return jsonify([vers_dict(d) for d in resultat]), 200


@tournois_bp.post("/tournois/<int:tournoi_id>/duels")
@role_requis(RoleUtilisateur.ADMIN)
def enregistrer_duel(tournoi_id):
    """Enregistre un duel déjà joué (vainqueur inclus) plutôt que de
    modéliser une "programmation" du duel suivie d'une saisie du résultat
    : le cahier des charges parle d'"enregistrer les duels au fur et à
    mesure", ce qui correspond à consigner un fait accompli.
    """
    tournoi = db.session.get(Tournoi, tournoi_id)
    if tournoi is None:
        return jsonify({"erreur": f"Tournoi {tournoi_id} introuvable."}), 404
    if tournoi.cloture_le is not None:
        return jsonify({"erreur": "Ce tournoi est déjà clôturé."}), 400

    donnees, erreur = valider(DuelSchema(), request.get_json(silent=True))
    if erreur:
        return erreur

    for eleve_id in (donnees["eleve_1_id"], donnees["eleve_2_id"]):
        if db.session.get(Eleve, eleve_id) is None:
            return jsonify({"erreur": f"Élève {eleve_id} introuvable."}), 400

    duel = Duel(tournoi_id=tournoi_id, **donnees)
    db.session.add(duel)
    db.session.commit()
    return jsonify(_serialize_duel(duel)), 201


@tournois_bp.post("/tournois/<int:tournoi_id>/cloture")
@role_requis(RoleUtilisateur.ADMIN)
def cloturer_tournoi(tournoi_id):
    """Détermine le vainqueur global (le plus de victoires en duel dans ce
    tournoi), débloque les compétences à condition "tournoi" pour ce
    vainqueur, et ajoute des points de réputation à sa maison.

    Refusé (400) si le tournoi est déjà clôturé — `cloture_le` sert de
    garde anti-rejeu, sur le même principe que la clôture d'année du jour
    4 (voir le docstring du modèle Tournoi) : relancer la clôture d'un
    tournoi déjà tranché ne doit pas pouvoir changer le vainqueur en
    douce si de nouveaux duels ont été ajoutés entre-temps par erreur.

    Sur une égalité stricte entre plusieurs élèves au nombre de victoires,
    aucun vainqueur n'est désigné automatiquement (400, avec la liste des
    ex æquo) : le cahier des charges ne dit rien du départage, et trancher
    au hasard ou par id serait arbitraire sur une décision qui affecte la
    réputation d'une maison. Mieux vaut un duel de plus pour départager
    que biaiser le résultat en silence.
    """
    tournoi = db.session.get(Tournoi, tournoi_id)
    if tournoi is None:
        return jsonify({"erreur": f"Tournoi {tournoi_id} introuvable."}), 404
    if tournoi.cloture_le is not None:
        return jsonify({"erreur": "Ce tournoi est déjà clôturé."}), 400

    duels = db.session.query(Duel).filter_by(tournoi_id=tournoi_id).all()
    if not duels:
        return jsonify({"erreur": "Aucun duel enregistré pour ce tournoi : rien à clôturer."}), 400

    victoires = Counter(d.vainqueur_id for d in duels if d.vainqueur_id is not None)
    if not victoires:
        return jsonify({"erreur": "Aucun duel de ce tournoi n'a de vainqueur enregistré."}), 400

    max_victoires = max(victoires.values())
    finalistes = sorted(eleve_id for eleve_id, n in victoires.items() if n == max_victoires)
    if len(finalistes) > 1:
        return (
            jsonify(
                {
                    "erreur": (
                        "Égalité entre plusieurs élèves au nombre de victoires : "
                        "impossible de désigner un vainqueur automatiquement."
                    ),
                    "eleves_ex_aequo": finalistes,
                    "victoires": max_victoires,
                }
            ),
            400,
        )

    vainqueur_id = finalistes[0]
    vainqueur = db.session.get(Eleve, vainqueur_id)

    tournoi.vainqueur_eleve_id = vainqueur_id
    tournoi.cloture_le = datetime.utcnow()

    competences_tournoi = (
        db.session.query(Competence).filter_by(condition_type=SourceDeblocage.TOURNOI).all()
    )
    competences_debloquees = []
    for competence in competences_tournoi:
        deja_obtenue = (
            db.session.query(Maitrise)
            .filter_by(eleve_id=vainqueur_id, competence_id=competence.id)
            .one_or_none()
        )
        if deja_obtenue is None:
            db.session.add(
                Maitrise(
                    eleve_id=vainqueur_id,
                    competence_id=competence.id,
                    date_obtention=date.today(),
                    source=SourceDeblocage.TOURNOI,
                    source_tournoi_id=tournoi_id,
                )
            )
            competences_debloquees.append(competence.nom)

    vainqueur.maison.reputation += POINTS_REPUTATION_VICTOIRE_TOURNOI

    db.session.commit()

    dto = ClotureTournoiDTO(
        tournoi_id=tournoi_id,
        vainqueur_eleve_id=vainqueur_id,
        victoires=max_victoires,
        competences_debloquees=competences_debloquees,
        maison_id=vainqueur.maison_id,
        reputation_ajoutee=POINTS_REPUTATION_VICTOIRE_TOURNOI,
        nouvelle_reputation=vainqueur.maison.reputation,
    )
    return jsonify(vers_dict(dto)), 200

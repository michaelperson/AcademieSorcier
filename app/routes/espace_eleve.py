"""
Espace élève : "mes cours", "mes notes", "mon dossier" (jour 2), puis "mes
compétences" et "mes tournois" (jour 3). Chaque vue est scopée sur
g.utilisateur_courant.eleve_id — jamais sur un id pris dans l'URL ou le
payload — pour qu'un élève ne puisse structurellement pas lire les
données d'un autre en changeant un paramètre.

Sortie typée (bonus) : voir app/dal/dto/espace_eleve.py::MonCoursDTO,
MaNoteDTO, MonDossierDTO, MaCompetenceDTO, MonDuelDTO.
"""

from flask import Blueprint, g, jsonify
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from app.auth import role_requis
from app.dal.dto import EleveMinimalDTO, MaCompetenceDTO, MaNoteDTO, MonCoursDTO, MonDossierDTO, MonDuelDTO, vers_dict
from app.extensions import db
from app.dal.models import Cours, Duel, Eleve, Inscription, Maitrise, Resultat
from app.dal.models.enums import RoleUtilisateur

espace_eleve_bp = Blueprint("espace_eleve", __name__, url_prefix="/moi")


def _eleve_courant() -> Eleve:
    return db.session.get(Eleve, g.utilisateur_courant.eleve_id)


@espace_eleve_bp.get("/cours")
@role_requis(RoleUtilisateur.ELEVE)
def mes_cours():
    inscriptions = (
        db.session.query(Inscription).filter_by(eleve_id=g.utilisateur_courant.eleve_id).all()
    )
    resultat = []
    for inscription in inscriptions:
        cours = db.session.get(Cours, inscription.cours_id)
        resultat.append(
            MonCoursDTO(
                cours_id=cours.id,
                intitule=cours.intitule,
                statut_inscription=inscription.statut.value,
                date_inscription=inscription.date_inscription.isoformat(),
            )
        )
    return jsonify([vers_dict(r) for r in resultat]), 200


@espace_eleve_bp.get("/notes")
@role_requis(RoleUtilisateur.ELEVE)
def mes_notes():
    resultats = (
        db.session.query(Resultat).filter_by(eleve_id=g.utilisateur_courant.eleve_id).all()
    )
    resultat = []
    for r in resultats:
        resultat.append(
            MaNoteDTO(
                examen_id=r.examen_id,
                titre_examen=r.examen.titre,
                cours_id=r.examen.cours_id,
                note=r.note,
                statut=r.statut.value if r.statut else None,
            )
        )
    return jsonify([vers_dict(r) for r in resultat]), 200


@espace_eleve_bp.get("/dossier")
@role_requis(RoleUtilisateur.ELEVE)
def mon_dossier():
    eleve = _eleve_courant()
    if eleve is None:
        return jsonify({"erreur": "Dossier introuvable pour cet utilisateur."}), 404

    dto = MonDossierDTO(
        id=eleve.id,
        nom=eleve.nom,
        annee_etude=eleve.annee_etude,
        maison=eleve.maison.nom,
        familier=eleve.familier,
        statut=eleve.statut.value,
        nombre_cours=len(eleve.inscriptions),
        nombre_notes=len(eleve.resultats),
    )
    return jsonify(vers_dict(dto)), 200


@espace_eleve_bp.get("/competences")
@role_requis(RoleUtilisateur.ELEVE)
def mes_competences():
    """Compétences débloquées par l'élève courant (jour 3)."""
    maitrises = (
        db.session.query(Maitrise)
        .filter_by(eleve_id=g.utilisateur_courant.eleve_id)
        .options(joinedload(Maitrise.competence))
        .all()
    )
    resultat = [
        MaCompetenceDTO(
            competence_id=m.competence_id,
            nom=m.competence.nom,
            categorie=m.competence.categorie,
            date_obtention=m.date_obtention.isoformat(),
            source=m.source.value,
        )
        for m in maitrises
    ]
    return jsonify([vers_dict(r) for r in resultat]), 200


@espace_eleve_bp.get("/tournois")
@role_requis(RoleUtilisateur.ELEVE)
def mes_tournois():
    """Historique des duels de l'élève courant, avec le résultat de chacun
    (gagné/perdu) et le tournoi concerné (jour 3).

    joinedload sur tournoi + les deux adversaires : cette vue boucle sur
    une liste de duels pour en tirer nom du tournoi et de l'adversaire,
    exactement le genre d'accès qui tournerait en N+1 sans ça (voir
    PERFORMANCE.md).
    """
    eleve_id = g.utilisateur_courant.eleve_id
    duels = (
        db.session.query(Duel)
        .filter(or_(Duel.eleve_1_id == eleve_id, Duel.eleve_2_id == eleve_id))
        .options(
            joinedload(Duel.tournoi),
            joinedload(Duel.eleve_1),
            joinedload(Duel.eleve_2),
        )
        .all()
    )

    resultat = []
    for duel in duels:
        adversaire = duel.eleve_2 if duel.eleve_1_id == eleve_id else duel.eleve_1
        if duel.vainqueur_id is None:
            issue = "en_attente"
        elif duel.vainqueur_id == eleve_id:
            issue = "gagne"
        else:
            issue = "perdu"

        resultat.append(
            MonDuelDTO(
                duel_id=duel.id,
                tournoi_id=duel.tournoi_id,
                tournoi_nom=duel.tournoi.nom,
                adversaire=EleveMinimalDTO(id=adversaire.id, nom=adversaire.nom),
                issue=issue,
            )
        )

    return jsonify([vers_dict(r) for r in resultat]), 200

"""
Espace élève du jour 2 : "mes cours", "mes notes", "mon dossier". Chaque
vue est scopée sur g.utilisateur_courant.eleve_id — jamais sur un id pris
dans l'URL ou le payload — pour qu'un élève ne puisse structurellement pas
lire les données d'un autre en changeant un paramètre.
"""

from flask import Blueprint, g, jsonify

from app.auth import role_requis
from app.extensions import db
from app.models import Cours, Eleve, Inscription, Resultat
from app.models.enums import RoleUtilisateur

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
            {
                "cours_id": cours.id,
                "intitule": cours.intitule,
                "statut_inscription": inscription.statut.value,
                "date_inscription": inscription.date_inscription.isoformat(),
            }
        )
    return jsonify(resultat), 200


@espace_eleve_bp.get("/notes")
@role_requis(RoleUtilisateur.ELEVE)
def mes_notes():
    resultats = (
        db.session.query(Resultat).filter_by(eleve_id=g.utilisateur_courant.eleve_id).all()
    )
    resultat = []
    for r in resultats:
        resultat.append(
            {
                "examen_id": r.examen_id,
                "titre_examen": r.examen.titre,
                "cours_id": r.examen.cours_id,
                "note": r.note,
                "statut": r.statut.value if r.statut else None,
            }
        )
    return jsonify(resultat), 200


@espace_eleve_bp.get("/dossier")
@role_requis(RoleUtilisateur.ELEVE)
def mon_dossier():
    eleve = _eleve_courant()
    if eleve is None:
        return jsonify({"erreur": "Dossier introuvable pour cet utilisateur."}), 404

    return (
        jsonify(
            {
                "id": eleve.id,
                "nom": eleve.nom,
                "annee_etude": eleve.annee_etude,
                "maison": eleve.maison.nom,
                "familier": eleve.familier,
                "statut": eleve.statut.value,
                "nombre_cours": len(eleve.inscriptions),
                "nombre_notes": len(eleve.resultats),
            }
        ),
        200,
    )

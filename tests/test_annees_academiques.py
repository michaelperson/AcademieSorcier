"""
Passage de fin d'année (jour 4) : l'endpoint métier le plus dense du
projet. On construit ici trois profils d'élèves directement en base
(plutôt que de rejouer toute la chaîne inscription -> résultats ->
clôture d'examen -> clôture de cours) pour isoler ce qu'on veut vraiment
tester : la décision de passage d'année elle-même, à partir d'une
inscription VALIDE et d'une moyenne connue.
"""

from datetime import date

from app.extensions import db
from app.dal.models import Eleve, Examen, Inscription, Resultat
from app.dal.models.enums import StatutEleve, StatutInscription


def _entetes_admin(utilisateur_admin):
    return {"X-User-Id": str(utilisateur_admin.id)}


def _eleve_avec_inscription_validee(maison, cours, annee_etude, note, nom):
    """Crée un élève avec une inscription VALIDE à `cours` et un résultat
    (donc une moyenne générale connue) sur cette inscription.
    """
    eleve = Eleve(nom=nom, annee_etude=annee_etude, maison_id=maison.id)
    db.session.add(eleve)
    db.session.commit()

    examen = db.session.query(Examen).filter_by(cours_id=cours.id).one_or_none()
    if examen is None:
        examen = Examen(
            cours_id=cours.id,
            titre=f"Examen de {cours.intitule}",
            date=date(2026, 5, 1),
            seuil_reussite=10.0,
        )
        db.session.add(examen)
        db.session.commit()

    db.session.add(
        Inscription(
            eleve_id=eleve.id,
            cours_id=cours.id,
            date_inscription=date(2025, 9, 1),
            statut=StatutInscription.VALIDE,
        )
    )
    db.session.add(Resultat(eleve_id=eleve.id, examen_id=examen.id, note=note))
    db.session.commit()
    return eleve


def test_cloture_annee_trois_issues(client, annee_academique, maison, cours, utilisateur_admin):
    """Les trois issues du cahier des charges, sur trois profils
    différents : moyenne haute + année < 7 -> promu ; moyenne basse ->
    redouble ; moyenne haute + année 7 -> diplômé (et archivé, pas
    supprimé : son dossier reste consultable).
    """
    eleve_promu = _eleve_avec_inscription_validee(maison, cours, annee_etude=3, note=16, nom="Elève Promu")
    eleve_redouble = _eleve_avec_inscription_validee(maison, cours, annee_etude=3, note=6, nom="Elève Redouble")
    eleve_diplome = _eleve_avec_inscription_validee(maison, cours, annee_etude=7, note=16, nom="Elève Diplome")

    reponse = client.post(
        f"/annees-academiques/{annee_academique.id}/cloture?seuil=12",
        headers=_entetes_admin(utilisateur_admin),
    )
    assert reponse.status_code == 200
    decisions = {d["eleve_id"]: d for d in reponse.get_json()["decisions"]}

    assert decisions[eleve_promu.id]["decision"] == "promu"
    assert decisions[eleve_promu.id]["annee_etude_avant"] == 3
    assert decisions[eleve_promu.id]["annee_etude_apres"] == 4

    assert decisions[eleve_redouble.id]["decision"] == "redouble"
    assert decisions[eleve_redouble.id]["annee_etude_apres"] == 3

    assert decisions[eleve_diplome.id]["decision"] == "diplome"
    assert decisions[eleve_diplome.id]["statut_apres"] == "diplome"

    db.session.refresh(eleve_diplome)
    assert eleve_diplome.statut == StatutEleve.DIPLOME
    # Archivé, pas supprimé : le dossier reste lisible normalement.
    fiche = client.get(f"/eleves/{eleve_diplome.id}")
    assert fiche.status_code == 200
    assert fiche.get_json()["statut"] == "diplome"


def test_cloture_annee_refuse_un_second_rejeu(client, annee_academique, utilisateur_admin):
    entetes = _entetes_admin(utilisateur_admin)
    premiere = client.post(f"/annees-academiques/{annee_academique.id}/cloture", headers=entetes)
    assert premiere.status_code == 200

    seconde = client.post(f"/annees-academiques/{annee_academique.id}/cloture", headers=entetes)
    assert seconde.status_code == 400


def test_cloture_annee_sans_inscription_validee_redouble(client, annee_academique, maison, utilisateur_admin):
    """Choix de conception documenté dans app/routes/annees_academiques.py :
    un élève actif sans aucune inscription validée cette année-là redouble
    par défaut, plutôt que d'être promu faute de preuve du contraire.
    """
    eleve = Eleve(nom="Élève Sans Cours Validé", annee_etude=3, maison_id=maison.id)
    db.session.add(eleve)
    db.session.commit()

    reponse = client.post(
        f"/annees-academiques/{annee_academique.id}/cloture",
        headers=_entetes_admin(utilisateur_admin),
    )
    assert reponse.status_code == 200
    decisions = {d["eleve_id"]: d for d in reponse.get_json()["decisions"]}
    assert decisions[eleve.id]["decision"] == "redouble"
    assert decisions[eleve.id]["moyenne_generale"] is None


def test_cloture_annee_refusee_sans_admin(client, annee_academique, utilisateur_eleve):
    reponse = client.post(
        f"/annees-academiques/{annee_academique.id}/cloture",
        headers={"X-User-Id": str(utilisateur_eleve.id)},
    )
    assert reponse.status_code == 403


def test_cloture_annee_introuvable(client, utilisateur_admin):
    reponse = client.post(
        "/annees-academiques/9999/cloture", headers=_entetes_admin(utilisateur_admin)
    )
    assert reponse.status_code == 404

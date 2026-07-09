from datetime import date

from flask import Blueprint, jsonify, request

from app.dal.dto import (
    ClotureExamenDTO,
    CoursResumeDTO,
    DecisionClotureCoursDTO,
    EleveRapportCoursDTO,
    EleveResumeDTO,
    EvaluerCompetencesDTO,
    ExamenDTO,
    MaitriseEntreeDTO,
    RapportClotureCoursDTO,
    ResultatClotureDTO,
    ResultatDTO,
    ResultatExamenDTO,
    vers_dict,
)
from app.extensions import db
from app.dal.models import Competence, Cours, Examen, Inscription, Maitrise, Resultat
from app.dal.models.enums import SourceDeblocage, StatutInscription, StatutResultat
from app.routes.inscriptions import STATUTS_OCCUPANT_UNE_PLACE
from app.schemas import ExamenModificationSchema, ExamenSchema, ResultatsEcritureSchema
from app.validation import valider

examens_bp = Blueprint("examens", __name__)


def _construire_dto_examen(examen: Examen) -> ExamenDTO:
    return ExamenDTO(
        id=examen.id,
        cours_id=examen.cours_id,
        titre=examen.titre,
        date=examen.date.isoformat(),
        seuil_reussite=examen.seuil_reussite,
    )


def _serialize_examen(examen: Examen) -> dict:
    return vers_dict(_construire_dto_examen(examen))


def _construire_dto_resultat(resultat: Resultat) -> ResultatDTO:
    return ResultatDTO(
        id=resultat.id,
        eleve_id=resultat.eleve_id,
        examen_id=resultat.examen_id,
        note=resultat.note,
        statut=resultat.statut.value if resultat.statut else None,
    )


def _serialize_resultat(resultat: Resultat) -> dict:
    return vers_dict(_construire_dto_resultat(resultat))


@examens_bp.get("/cours/<int:cours_id>/examens")
def lister_examens_du_cours(cours_id):
    if db.session.get(Cours, cours_id) is None:
        return jsonify({"erreur": f"Cours {cours_id} introuvable."}), 404

    examens = db.session.query(Examen).filter_by(cours_id=cours_id).order_by(Examen.date).all()
    return jsonify([_serialize_examen(e) for e in examens]), 200


@examens_bp.post("/cours/<int:cours_id>/examens")
def creer_examen(cours_id):
    if db.session.get(Cours, cours_id) is None:
        return jsonify({"erreur": f"Cours {cours_id} introuvable."}), 404

    donnees, erreur = valider(ExamenSchema(), request.get_json(silent=True))
    if erreur:
        return erreur

    examen = Examen(
        cours_id=cours_id,
        titre=donnees["titre"],
        date=donnees["date"],
        seuil_reussite=donnees["seuil_reussite"],
    )
    db.session.add(examen)
    db.session.commit()
    return jsonify(_serialize_examen(examen)), 201


@examens_bp.get("/examens/<int:examen_id>")
def obtenir_examen(examen_id):
    examen = db.session.get(Examen, examen_id)
    if examen is None:
        return jsonify({"erreur": f"Examen {examen_id} introuvable."}), 404
    return jsonify(_serialize_examen(examen)), 200


@examens_bp.put("/examens/<int:examen_id>")
def modifier_examen(examen_id):
    examen = db.session.get(Examen, examen_id)
    if examen is None:
        return jsonify({"erreur": f"Examen {examen_id} introuvable."}), 404

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    donnees, erreur = valider(ExamenModificationSchema(), payload, partial=True)
    if erreur:
        return erreur

    for champ, valeur in donnees.items():
        setattr(examen, champ, valeur)

    db.session.commit()
    return jsonify(_serialize_examen(examen)), 200


@examens_bp.delete("/examens/<int:examen_id>")
def supprimer_examen(examen_id):
    examen = db.session.get(Examen, examen_id)
    if examen is None:
        return jsonify({"erreur": f"Examen {examen_id} introuvable."}), 404

    db.session.delete(examen)
    db.session.commit()
    return jsonify({"message": f"Examen {examen_id} supprimé."}), 200


@examens_bp.post("/examens/<int:examen_id>/resultats")
def saisir_resultats(examen_id):
    """Saisie en masse : un seul payload avec la liste des notes, pas un
    appel par élève. Validation atomique — si une seule entrée est
    invalide, rien n'est écrit en base (pas de saisie à moitié appliquée).

    Depuis le jour 4, la forme du payload (présence des champs, notes
    entre 0 et 20) est vérifiée par ResultatsEcritureSchema — voir
    app/schemas.py. Ce qui reste vérifié ici, à la main : que chaque
    eleve_id correspond bien à un élève inscrit au cours de cet examen,
    une règle qui dépend de l'état de la base et pas seulement de la
    forme du payload.

    Réécrire la note d'un élève qui avait déjà un résultat remet son
    `statut` à `None` : la décision réussi/échec datait de l'ancienne note
    et ne veut plus rien dire une fois celle-ci changée. Il faut re-clôturer
    l'examen (POST /examens/<id>/cloture) pour la refixer.
    """
    examen = db.session.get(Examen, examen_id)
    if examen is None:
        return jsonify({"erreur": f"Examen {examen_id} introuvable."}), 404

    donnees, erreur = valider(ResultatsEcritureSchema(), request.get_json(silent=True))
    if erreur:
        return erreur

    inscrits_au_cours = {
        i.eleve_id
        for i in db.session.query(Inscription).filter_by(cours_id=examen.cours_id).all()
    }

    erreurs = []
    entrees_validees = []
    for entree in donnees["resultats"]:
        eleve_id = entree["eleve_id"]
        note = entree["note"]
        if eleve_id not in inscrits_au_cours:
            erreurs.append(
                {
                    "eleve_id": eleve_id,
                    "erreur": "cet élève n'est pas inscrit au cours de cet examen.",
                }
            )
            continue
        entrees_validees.append((eleve_id, note))

    if erreurs:
        return jsonify({"erreur": "Payload invalide.", "details": erreurs}), 400

    resultats_ecrits = []
    for eleve_id, note in entrees_validees:
        resultat = (
            db.session.query(Resultat)
            .filter_by(eleve_id=eleve_id, examen_id=examen_id)
            .one_or_none()
        )
        if resultat is None:
            resultat = Resultat(eleve_id=eleve_id, examen_id=examen_id, note=note)
            db.session.add(resultat)
        else:
            resultat.note = note
            resultat.statut = None
        resultats_ecrits.append(resultat)

    db.session.commit()
    return jsonify([_serialize_resultat(r) for r in resultats_ecrits]), 201


@examens_bp.get("/examens/<int:examen_id>/resultats")
def lister_resultats_examen(examen_id):
    if db.session.get(Examen, examen_id) is None:
        return jsonify({"erreur": f"Examen {examen_id} introuvable."}), 404

    resultats = db.session.query(Resultat).filter_by(examen_id=examen_id).all()
    return jsonify([_serialize_resultat(r) for r in resultats]), 200


@examens_bp.post("/examens/<int:examen_id>/cloture")
def cloturer_examen(examen_id):
    """Clôture d'UN examen.

    Décide, pour chaque élève qui l'a passé, s'il a réussi ou échoué CET
    examen précis — un jugement qui ne regarde que la note à cet examen et
    son seuil de réussite à lui, indépendamment du reste du cours. La
    décision est écrite sur `Resultat.statut`.

    Ce n'est PAS la même chose que le statut de l'inscription au cours
    (`Inscription.statut`), qui se décide sur la moyenne de TOUS les
    examens du cours et se met à jour ailleurs, via l'endpoint séparé
    POST /cours/<id>/cloture. Un élève peut échouer un examen ponctuel et
    rester "en_cours" dans le cours si sa moyenne générale suffit — les
    deux statuts vivent sur deux entités différentes exprès (voir
    Resultat.statut et Inscription.statut).

    Refuse la clôture (400) tant qu'un élève qui occupe une place dans le
    cours n'a pas de résultat pour cet examen : sans note, il n'y a rien à
    juger pour lui, et clôturer quand même reviendrait à décider à sa
    place. Rejouer la clôture sur les mêmes notes redonne les mêmes
    statuts (idempotent).
    """
    examen = db.session.get(Examen, examen_id)
    if examen is None:
        return jsonify({"erreur": f"Examen {examen_id} introuvable."}), 404

    resultats_examen = db.session.query(Resultat).filter_by(examen_id=examen_id).all()
    if not resultats_examen:
        return jsonify({"erreur": "Aucun résultat saisi pour cet examen : rien à clôturer."}), 400

    eleves_du_cours = {
        i.eleve_id
        for i in db.session.query(Inscription)
        .filter(
            Inscription.cours_id == examen.cours_id,
            Inscription.statut.in_(STATUTS_OCCUPANT_UNE_PLACE),
        )
        .all()
    }
    eleves_avec_resultat = {r.eleve_id for r in resultats_examen}
    eleves_manquants = sorted(eleves_du_cours - eleves_avec_resultat)
    if eleves_manquants:
        return (
            jsonify(
                {
                    "erreur": (
                        "Tous les élèves du cours n'ont pas encore de résultat "
                        "pour cet examen : clôture refusée."
                    ),
                    "eleves_sans_resultat": eleves_manquants,
                }
            ),
            400,
        )

    for resultat in resultats_examen:
        resultat.statut = (
            StatutResultat.REUSSI
            if resultat.note >= examen.seuil_reussite
            else StatutResultat.ECHEC
        )

    db.session.commit()

    moyenne_examen = sum(r.note for r in resultats_examen) / len(resultats_examen)

    dto = ClotureExamenDTO(
        examen_id=examen_id,
        seuil_reussite=examen.seuil_reussite,
        moyenne_examen=round(moyenne_examen, 2),
        resultats=[
            ResultatClotureDTO(eleve_id=r.eleve_id, note=r.note, statut=r.statut.value)
            for r in resultats_examen
        ],
    )
    return jsonify(vers_dict(dto)), 200


@examens_bp.post("/examens/<int:examen_id>/evaluer-competences")
def evaluer_competences(examen_id):
    """Endpoint métier du jour 3 : après la clôture d'un examen, débloque
    automatiquement les compétences dont la condition est liée à CET
    examen, pour chaque élève dont la note atteint le seuil requis par la
    compétence (Competence.note_min — pas forcément le même seuil que
    Examen.seuil_reussite : une compétence peut exiger mieux que la simple
    moyenne).

    Exige que l'examen ait déjà été clôturé (chaque résultat a un statut) :
    évaluer des compétences sur des résultats pas encore validés reviendrait
    à débloquer quelque chose sur une note qui pourrait encore changer.

    Idempotent par construction : la contrainte unique (eleve_id,
    competence_id) sur Maitrise empêche toute création en double, donc
    relancer cet endpoint après un premier passage ne fait que déplacer les
    élèves déjà débloqués de "maitrises_creees" à "deja_debloquees", sans
    jamais dupliquer une ligne.
    """
    examen = db.session.get(Examen, examen_id)
    if examen is None:
        return jsonify({"erreur": f"Examen {examen_id} introuvable."}), 404

    resultats = db.session.query(Resultat).filter_by(examen_id=examen_id).all()
    if not resultats:
        return jsonify({"erreur": "Aucun résultat saisi pour cet examen."}), 400
    if any(r.statut is None for r in resultats):
        return (
            jsonify(
                {
                    "erreur": (
                        "Cet examen doit d'abord être clôturé "
                        "(POST /examens/<id>/cloture) avant d'évaluer les compétences."
                    )
                }
            ),
            400,
        )

    competences = (
        db.session.query(Competence)
        .filter_by(condition_type=SourceDeblocage.EXAMEN, examen_id=examen_id)
        .all()
    )

    maitrises_creees = []
    deja_debloquees = []
    for competence in competences:
        for resultat in resultats:
            if resultat.note < competence.note_min:
                continue

            existante = (
                db.session.query(Maitrise)
                .filter_by(eleve_id=resultat.eleve_id, competence_id=competence.id)
                .one_or_none()
            )
            entree = MaitriseEntreeDTO(eleve_id=resultat.eleve_id, competence=competence.nom)
            if existante is None:
                db.session.add(
                    Maitrise(
                        eleve_id=resultat.eleve_id,
                        competence_id=competence.id,
                        date_obtention=date.today(),
                        source=SourceDeblocage.EXAMEN,
                        source_examen_id=examen_id,
                    )
                )
                maitrises_creees.append(entree)
            else:
                deja_debloquees.append(entree)

    db.session.commit()

    dto = EvaluerCompetencesDTO(
        examen_id=examen_id,
        competences_evaluees=[c.nom for c in competences],
        maitrises_creees=maitrises_creees,
        deja_debloquees=deja_debloquees,
    )
    return jsonify(vers_dict(dto)), 200


def _resultats_eleve_dans_cours(eleve_id, cours_id):
    return (
        db.session.query(Resultat)
        .join(Examen, Resultat.examen_id == Examen.id)
        .filter(Examen.cours_id == cours_id, Resultat.eleve_id == eleve_id)
        .all()
    )


def _moyenne_et_statut(resultats):
    """Moyenne d'un élève sur les examens qu'il a passés dans un cours, et
    décision réussi/échec associée.

    Le seuil retenu est la moyenne des `seuil_reussite` de ces mêmes
    examens. Il n'existe pas de seuil au niveau du cours en base — seul
    `Examen.seuil_reussite` existe — donc plutôt que d'inventer une
    nouvelle valeur non demandée par le cahier des charges, ce seuil se
    déduit de ce qui a déjà été saisi par le professeur, examen par
    examen.
    """
    if not resultats:
        return None, None, None
    moyenne = sum(r.note for r in resultats) / len(resultats)
    seuil_moyen = sum(r.examen.seuil_reussite for r in resultats) / len(resultats)
    statut = StatutResultat.REUSSI if moyenne >= seuil_moyen else StatutResultat.ECHEC
    return round(moyenne, 2), round(seuil_moyen, 2), statut


def _rapport_cloture_cours(cours: Cours):
    inscriptions = (
        db.session.query(Inscription)
        .filter(
            Inscription.cours_id == cours.id,
            Inscription.statut.in_(STATUTS_OCCUPANT_UNE_PLACE),
        )
        .all()
    )

    eleves = []
    for inscription in inscriptions:
        eleve = inscription.eleve
        moyenne, _seuil_moyen, statut = _moyenne_et_statut(
            _resultats_eleve_dans_cours(eleve.id, cours.id)
        )
        eleves.append(
            EleveRapportCoursDTO(
                eleve_id=eleve.id,
                nom=eleve.nom,
                moyenne=moyenne,
                statut=statut.value if statut else None,
            )
        )

    dto = RapportClotureCoursDTO(
        cours_id=cours.id,
        intitule=cours.intitule,
        annee_academique=cours.annee_academique.libelle,
        eleves=eleves,
    )
    return jsonify(vers_dict(dto)), 200


def _decider_cloture_cours(cours: Cours, eleve_id: int):
    inscription = (
        db.session.query(Inscription)
        .filter_by(cours_id=cours.id, eleve_id=eleve_id)
        .one_or_none()
    )
    if inscription is None:
        return jsonify({"erreur": f"Élève {eleve_id} non inscrit à ce cours."}), 404

    resultats = _resultats_eleve_dans_cours(eleve_id, cours.id)
    if not resultats:
        return (
            jsonify(
                {"erreur": "Cet élève n'a encore aucun résultat dans ce cours : rien à clôturer."}
            ),
            400,
        )

    eleve = inscription.eleve
    moyenne, seuil_moyen, statut = _moyenne_et_statut(resultats)
    inscription.statut = (
        StatutInscription.VALIDE if statut == StatutResultat.REUSSI else StatutInscription.EN_COURS
    )
    db.session.commit()

    dto = DecisionClotureCoursDTO(
        cours=CoursResumeDTO(
            id=cours.id, intitule=cours.intitule, annee_academique=cours.annee_academique.libelle
        ),
        eleve=EleveResumeDTO(id=eleve.id, nom=eleve.nom, maison=eleve.maison.nom),
        resultats=[
            ResultatExamenDTO(
                examen_id=r.examen_id,
                titre_examen=r.examen.titre,
                note=r.note,
                statut_examen=r.statut.value if r.statut else None,
            )
            for r in resultats
        ],
        moyenne_cours=moyenne,
        seuil_retenu=seuil_moyen,
        decision_finale=statut.value,
        nouveau_statut_inscription=inscription.statut.value,
    )
    return jsonify(vers_dict(dto)), 200


@examens_bp.post("/cours/<int:cours_id>/cloture")
def cloturer_cours(cours_id):
    """Endpoint supplémentaire du jour 2 : décide de la réussite d'un
    élève sur le COURS entier, à partir de la moyenne de tous les examens
    qu'il y a passés. C'est cette moyenne-là, et pas celle d'un examen
    isolé, qui met à jour `Inscription.statut` (voir `cloturer_examen`
    pour la clôture d'un examen, qui ne touche que `Resultat.statut`).

    Deux modes, choisis par la présence ou non de `?eleve_id=` :

    - Sans eleve_id : mode rapport, en lecture seule. Renvoie la moyenne
      et le statut calculés pour tous les élèves qui occupent une place
      dans le cours, sans rien écrire en base. Pensé pour qu'un
      professeur regarde où en est sa classe avant de clôturer élève par
      élève.
    - Avec eleve_id : met à jour l'inscription de CET élève seulement
      (VALIDE si réussi, EN_COURS si échec) et renvoie son dossier complet
      sur ce cours : fiche du cours, fiche de l'élève, note à chaque
      examen, décision finale.
    """
    cours = db.session.get(Cours, cours_id)
    if cours is None:
        return jsonify({"erreur": f"Cours {cours_id} introuvable."}), 404

    eleve_id_brut = request.args.get("eleve_id")
    if eleve_id_brut is None:
        return _rapport_cloture_cours(cours)

    try:
        eleve_id = int(eleve_id_brut)
    except ValueError:
        return jsonify({"erreur": "eleve_id doit être un entier."}), 400

    return _decider_cloture_cours(cours, eleve_id)

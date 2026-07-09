"""
Année académique et passage de fin d'année (jour 4) — l'endpoint métier le
plus dense du projet. CRUD léger (lecture publique, écriture admin, pas de
suppression : une année qui a déjà des cours rattachés n'a pas vocation à
disparaître) plus l'action de clôture proprement dite.

Le calcul de la moyenne générale d'un élève, pour cet endpoint, ne
retraverse PAS `_moyenne_et_statut` de app/routes/examens.py (moyenne des
résultats bruts d'un cours) mais s'appuie directement sur les cours dont
l'inscription est déjà VALIDE pour cette année : le passage de fin d'année
juge l'année scolaire dans son ensemble, cours par cours déjà tranchés
(voir POST /cours/<id>/cloture, jour 2), pas les notes brutes une par une.
Un élève qui n'a aucune inscription validée cette année n'a rien à faire
valoir : plutôt que de le promouvoir par défaut, il redouble (voir
_cloturer_annee, le choix est documenté sur place).

Sortie typée (bonus) : voir app/dal/dto/annees_academiques.py::AnneeAcademiqueDTO.

Documentation OpenAPI (bonus) : voir app/openapi_generator.py — chaque vue
porte son propre bloc YAML dans sa docstring.
"""

from collections import Counter, defaultdict
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from app.auth import role_requis
from app.dal.dto import AnneeAcademiqueDTO, vers_dict
from app.extensions import db
from app.dal.models import AnneeAcademique, Cours, Eleve, Examen, Inscription, Resultat
from app.dal.models.enums import RoleUtilisateur, StatutEleve, StatutInscription
from app.schemas import AnneeAcademiqueModificationSchema, AnneeAcademiqueSchema
from app.validation import valider

annees_bp = Blueprint("annees_academiques", __name__, url_prefix="/annees-academiques")


def _construire_dto(annee: AnneeAcademique) -> AnneeAcademiqueDTO:
    return AnneeAcademiqueDTO(
        id=annee.id,
        libelle=annee.libelle,
        seuil_promotion=annee.seuil_promotion,
        cloturee_le=annee.cloturee_le.isoformat() if annee.cloturee_le else None,
    )


def _serialize_annee(annee: AnneeAcademique) -> dict:
    return vers_dict(_construire_dto(annee))


@annees_bp.get("")
def lister_annees():
    """Liste les années académiques.
    ---
    get:
      tags:
        - Passage d'année
      summary: Lister les années académiques
      responses:
        200:
          description: Liste des années académiques.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/AnneeAcademique'
    """
    annees = db.session.query(AnneeAcademique).order_by(AnneeAcademique.libelle.desc()).all()
    return jsonify([_serialize_annee(a) for a in annees]), 200


@annees_bp.post("")
@role_requis(RoleUtilisateur.ADMIN)
def creer_annee():
    """Créer une année académique (admin).
    ---
    post:
      tags:
        - Passage d'année
      summary: Créer une année académique (admin)
      security:
        - XUserId: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AnneeAcademiqueEcriture'
      responses:
        201:
          description: Année créée.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AnneeAcademique'
        400:
          description: Payload invalide, ou libellé déjà utilisé.
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
    """
    donnees, erreur = valider(AnneeAcademiqueSchema(), request.get_json(silent=True))
    if erreur:
        return erreur

    if db.session.query(AnneeAcademique).filter_by(libelle=donnees["libelle"]).first() is not None:
        return jsonify({"erreur": f"Une année académique {donnees['libelle']!r} existe déjà."}), 400

    annee = AnneeAcademique(**donnees)
    db.session.add(annee)
    db.session.commit()
    return jsonify(_serialize_annee(annee)), 201


@annees_bp.get("/<int:annee_id>")
def obtenir_annee(annee_id):
    """Obtenir une année académique par id.
    ---
    get:
      tags:
        - Passage d'année
      summary: Obtenir une année académique
      parameters:
        - in: path
          name: annee_id
          required: true
          schema:
            type: integer
          example: 1
      responses:
        200:
          description: Année trouvée.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AnneeAcademique'
        404:
          description: Année académique introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    annee = db.session.get(AnneeAcademique, annee_id)
    if annee is None:
        return jsonify({"erreur": f"Année académique {annee_id} introuvable."}), 404
    return jsonify(_serialize_annee(annee)), 200


@annees_bp.put("/<int:annee_id>")
@role_requis(RoleUtilisateur.ADMIN)
def modifier_annee(annee_id):
    """Sert surtout à ajuster `seuil_promotion` — le "seuil configurable"
    du cahier des charges — avant de lancer la clôture. Refusé une fois
    l'année clôturée : changer le seuil rétroactivement rendrait la
    décision déjà prise incohérente avec la configuration affichée.
    ---
    put:
      tags:
        - Passage d'année
      summary: Ajuster le seuil de promotion avant la clôture (admin)
      description: "Refusé si l'année est déjà clôturée : la configuration est alors figée."
      security:
        - XUserId: []
      parameters:
        - in: path
          name: annee_id
          required: true
          schema:
            type: integer
          example: 1
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AnneeAcademiqueEcriture'
      responses:
        200:
          description: Année modifiée.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AnneeAcademique'
        400:
          description: Payload invalide, ou année déjà clôturée.
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
          description: Année académique introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    annee = db.session.get(AnneeAcademique, annee_id)
    if annee is None:
        return jsonify({"erreur": f"Année académique {annee_id} introuvable."}), 404
    if annee.cloturee_le is not None:
        return jsonify({"erreur": "Cette année est déjà clôturée : configuration figée."}), 400

    payload = request.get_json(silent=True)
    if not payload:
        return jsonify({"erreur": "Aucune donnée à mettre à jour."}), 400

    donnees, erreur = valider(AnneeAcademiqueModificationSchema(), payload, partial=True)
    if erreur:
        return erreur

    for champ, valeur in donnees.items():
        setattr(annee, champ, valeur)

    db.session.commit()
    return jsonify(_serialize_annee(annee)), 200


def _moyennes_generales(annee: AnneeAcademique, eleves_actifs):
    """Calcule, pour chaque élève actif, sa moyenne générale sur l'année :
    la moyenne des moyennes de cours pour lesquels son inscription est
    VALIDE cette année-là (voir le docstring du module pour pourquoi ce
    n'est pas la moyenne brute de tous ses résultats).

    Deux requêtes globales plutôt qu'une requête par élève : la chasse au
    N+1 vaut aussi pour un endpoint qui boucle sur des élèves, pas
    seulement pour un listing HTTP classique (voir PERFORMANCE.md,
    section jour 4).
    """
    inscriptions_validees = (
        db.session.query(Inscription)
        .join(Cours, Inscription.cours_id == Cours.id)
        .filter(
            Cours.annee_academique_id == annee.id,
            Inscription.statut == StatutInscription.VALIDE,
        )
        .all()
    )

    cours_valides_par_eleve = defaultdict(list)
    cours_ids = set()
    for inscription in inscriptions_validees:
        cours_valides_par_eleve[inscription.eleve_id].append(inscription.cours_id)
        cours_ids.add(inscription.cours_id)

    notes_par_eleve_cours = defaultdict(list)
    if cours_ids:
        lignes = (
            db.session.query(Resultat.eleve_id, Examen.cours_id, Resultat.note)
            .join(Examen, Resultat.examen_id == Examen.id)
            .filter(Examen.cours_id.in_(cours_ids))
            .all()
        )
        for eleve_id, cours_id, note in lignes:
            notes_par_eleve_cours[(eleve_id, cours_id)].append(note)

    moyennes = {}
    for eleve in eleves_actifs:
        moyennes_cours = []
        for cours_id in cours_valides_par_eleve.get(eleve.id, []):
            notes = notes_par_eleve_cours.get((eleve.id, cours_id), [])
            if notes:
                moyennes_cours.append(sum(notes) / len(notes))
        moyennes[eleve.id] = round(sum(moyennes_cours) / len(moyennes_cours), 2) if moyennes_cours else None

    return moyennes


@annees_bp.post("/<int:annee_id>/cloture")
@role_requis(RoleUtilisateur.ADMIN)
def cloturer_annee(annee_id):
    """Le passage de fin d'année. Pour chaque élève actif :

    - moyenne générale introuvable (aucune inscription validée cette
      année) : redoublement. Choix documenté, pas un oubli — un élève
      sans aucun cours validé n'a rien démontré cette année, le
      considérer promouvable par défaut serait plus étrange que
      l'inverse.
    - moyenne >= seuil et année < 7 : promotion (annee_etude + 1).
    - moyenne < seuil : redoublement (annee_etude inchangée).
    - moyenne >= seuil et année == 7 : diplomation (statut = diplome).
      L'élève n'est pas supprimé — son dossier, ses compétences et son
      historique de tournois restent consultables tels quels, comme
      l'exige le cahier des charges.

    Refusé (400) si l'année est déjà clôturée : `cloturee_le` sert de
    garde anti-rejeu, sur le même principe que `Tournoi.cloture_le`
    (jour 3) — sans ça, relancer l'opération par erreur repromouvrait ou
    re-diplômerait tout le monde une seconde fois.

    Le seuil retenu est `AnneeAcademique.seuil_promotion` par défaut,
    mais peut être court-circuité ponctuellement via `?seuil=` (sans
    modifier la valeur enregistrée) — pratique pour rejouer une
    simulation sans passer par PUT /annees-academiques/<id> à chaque
    essai.
    ---
    post:
      tags:
        - Passage d'année
      summary: Clôturer l'année (promotion, redoublement, diplomation)
      security:
        - XUserId: []
      description: >
        L'endpoint métier le plus dense du projet. Pour chaque élève actif :
        moyenne générale sur ses inscriptions VALIDE de l'année (null si
        aucune, traité comme un redoublement) comparée au seuil ; promotion
        si suffisante et année < 7, diplomation si suffisante et année == 7
        (l'élève passe en statut diplômé, archivé mais pas supprimé),
        redoublement sinon. Refusé (400) si l'année est déjà clôturée —
        garde anti-rejeu sur cloturee_le, même principe que
        Tournoi.cloture_le (jour 3).
      parameters:
        - in: path
          name: annee_id
          required: true
          schema:
            type: integer
          example: 1
        - in: query
          name: seuil
          required: false
          schema:
            type: number
          description: Court-circuite ponctuellement seuil_promotion sans modifier la valeur enregistrée.
      responses:
        200:
          description: Clôture effectuée.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ClotureAnneeReponse'
        400:
          description: Année déjà clôturée, ou seuil non numérique.
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
        404:
          description: Année académique introuvable.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Erreur'
    """
    annee = db.session.get(AnneeAcademique, annee_id)
    if annee is None:
        return jsonify({"erreur": f"Année académique {annee_id} introuvable."}), 404
    if annee.cloturee_le is not None:
        return jsonify({"erreur": "Cette année académique est déjà clôturée."}), 400

    seuil_brut = request.args.get("seuil")
    if seuil_brut is not None:
        try:
            seuil = float(seuil_brut)
        except ValueError:
            return jsonify({"erreur": "seuil doit être un nombre."}), 400
    else:
        seuil = annee.seuil_promotion

    eleves_actifs = (
        db.session.query(Eleve)
        .filter_by(statut=StatutEleve.ACTIF)
        .options(joinedload(Eleve.maison))
        .order_by(Eleve.id)
        .all()
    )

    moyennes = _moyennes_generales(annee, eleves_actifs)

    decisions = []
    for eleve in eleves_actifs:
        moyenne_generale = moyennes[eleve.id]
        annee_etude_avant = eleve.annee_etude

        if moyenne_generale is None or moyenne_generale < seuil:
            decision = "redouble"
        elif eleve.annee_etude >= 7:
            decision = "diplome"
            eleve.statut = StatutEleve.DIPLOME
        else:
            decision = "promu"
            eleve.annee_etude += 1

        decisions.append(
            {
                "eleve_id": eleve.id,
                "nom": eleve.nom,
                "moyenne_generale": moyenne_generale,
                "annee_etude_avant": annee_etude_avant,
                "annee_etude_apres": eleve.annee_etude,
                "decision": decision,
                "statut_apres": eleve.statut.value,
            }
        )

    annee.cloturee_le = datetime.utcnow()
    db.session.commit()

    compteurs = Counter(d["decision"] for d in decisions)

    return (
        jsonify(
            {
                "annee_academique_id": annee.id,
                "libelle": annee.libelle,
                "seuil_retenu": seuil,
                "nombre_eleves_actifs": len(eleves_actifs),
                "promus": compteurs.get("promu", 0),
                "redoublants": compteurs.get("redouble", 0),
                "diplomes": compteurs.get("diplome", 0),
                "decisions": decisions,
            }
        ),
        200,
    )

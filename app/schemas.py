"""
Schémas marshmallow — validation stricte des payloads d'écriture (jour 4).

Avant ce fichier, chaque route vérifiait ses champs à la main (voir par
exemple l'historique de app/routes/eleves.py) : ça marchait, mais avec
un message différent d'une route à l'autre et aucune garantie qu'on n'ait
pas oublié un cas limite quelque part. Centraliser dans des schémas fait
gagner deux choses concrètes : un format d'erreur identique partout
(voir app/validation.py) et des messages en français précis sur le champ
fautif, ce que demande explicitement le cahier des charges du jour 4.

Ce que marshmallow valide ici : types, présence, bornes numériques,
formats de date, valeurs d'énumération. Ce qu'il NE valide PAS (et qui
reste vérifié dans la route, après le passage du schéma) : l'existence
en base d'une clé étrangère (professeur_id, maison_id, examen_id...),
les règles qui dépendent de plusieurs lignes à la fois (capacité d'un
cours, double inscription, tournoi déjà clôturé...). Un schéma ne
connaît que la forme du payload, pas l'état de la base.
"""

from marshmallow import Schema, ValidationError, fields, validate, validates_schema

from app.dal.models.enums import SourceDeblocage, StatutEleve

MESSAGES_CHAMP = {
    "required": "Ce champ est requis.",
    "null": "Ce champ ne peut pas être vide.",
}
MESSAGES_TEXTE = {**MESSAGES_CHAMP, "invalid": "Doit être une chaîne de caractères."}
MESSAGES_ENTIER = {**MESSAGES_CHAMP, "invalid": "Doit être un nombre entier."}
MESSAGES_NOMBRE = {**MESSAGES_CHAMP, "invalid": "Doit être un nombre."}


def _erreur_bornes(minimum=None, maximum=None):
    if minimum is not None and maximum is not None:
        return f"Doit être compris entre {minimum} et {maximum}."
    if minimum is not None:
        return f"Doit être supérieur ou égal à {minimum}."
    return f"Doit être inférieur ou égal à {maximum}."


# ---------------------------------------------------------------- Maison --

class MaisonSchema(Schema):
    nom = fields.Str(required=True, validate=validate.Length(min=1, max=50), error_messages=MESSAGES_TEXTE)
    couleur = fields.Str(required=True, validate=validate.Length(min=1, max=30), error_messages=MESSAGES_TEXTE)
    fondateur = fields.Str(required=True, validate=validate.Length(min=1, max=100), error_messages=MESSAGES_TEXTE)
    valeurs = fields.Str(required=False, allow_none=True, validate=validate.Length(max=255), error_messages=MESSAGES_TEXTE)


# ----------------------------------------------------------- Professeur --

class ProfesseurSchema(Schema):
    nom = fields.Str(required=True, validate=validate.Length(min=1, max=100), error_messages=MESSAGES_TEXTE)
    matiere_enseignee = fields.Str(
        required=True, validate=validate.Length(min=1, max=100), error_messages=MESSAGES_TEXTE
    )
    anciennete = fields.Int(
        required=True,
        validate=validate.Range(min=0, max=80, error=_erreur_bornes(0, 80)),
        error_messages=MESSAGES_ENTIER,
    )


# ----------------------------------------------------------------- Cours --

class CoursSchema(Schema):
    intitule = fields.Str(required=True, validate=validate.Length(min=1, max=150), error_messages=MESSAGES_TEXTE)
    niveau_requis = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=7, error=_erreur_bornes(1, 7)),
        error_messages=MESSAGES_ENTIER,
    )
    capacite_max = fields.Int(
        required=True,
        validate=validate.Range(min=1, error=_erreur_bornes(1)),
        error_messages=MESSAGES_ENTIER,
    )
    professeur_id = fields.Int(required=True, error_messages=MESSAGES_ENTIER)


# ----------------------------------------------------------------- Eleve --

class EleveSchema(Schema):
    nom = fields.Str(required=True, validate=validate.Length(min=1, max=100), error_messages=MESSAGES_TEXTE)
    annee_etude = fields.Int(
        required=True,
        validate=validate.Range(min=1, max=7, error=_erreur_bornes(1, 7)),
        error_messages=MESSAGES_ENTIER,
    )
    maison_id = fields.Int(required=True, error_messages=MESSAGES_ENTIER)
    familier = fields.Str(required=False, allow_none=True, validate=validate.Length(max=100), error_messages=MESSAGES_TEXTE)
    statut = fields.Str(
        required=False,
        validate=validate.OneOf(
            [s.value for s in StatutEleve],
            error="Valeur invalide : choisir parmi {choices}.",
        ),
        error_messages=MESSAGES_TEXTE,
    )


# ------------------------------------------------------------ Inscription --

class InscriptionSchema(Schema):
    eleve_id = fields.Int(required=True, error_messages=MESSAGES_ENTIER)


# ----------------------------------------------------------------- Examen --

class ExamenSchema(Schema):
    titre = fields.Str(required=True, validate=validate.Length(min=1, max=150), error_messages=MESSAGES_TEXTE)
    date = fields.Date(
        required=True,
        format="%Y-%m-%d",
        error_messages={**MESSAGES_CHAMP, "invalid": "Doit être une date au format AAAA-MM-JJ."},
    )
    seuil_reussite = fields.Float(
        required=True,
        validate=validate.Range(min=0, max=20, error=_erreur_bornes(0, 20)),
        error_messages=MESSAGES_NOMBRE,
    )


class ExamenModificationSchema(ExamenSchema):
    """PUT /examens/<id> : les trois champs restent optionnels (mise à
    jour partielle), mais gardent les mêmes bornes une fois présents.
    """
    titre = fields.Str(required=False, validate=validate.Length(min=1, max=150), error_messages=MESSAGES_TEXTE)
    date = fields.Date(
        required=False,
        format="%Y-%m-%d",
        error_messages={**MESSAGES_CHAMP, "invalid": "Doit être une date au format AAAA-MM-JJ."},
    )
    seuil_reussite = fields.Float(
        required=False,
        validate=validate.Range(min=0, max=20, error=_erreur_bornes(0, 20)),
        error_messages=MESSAGES_NOMBRE,
    )


# ------------------------------------------------------ Résultats en masse --

NOTE_MIN = 0
NOTE_MAX = 20


class ResultatEntreeSchema(Schema):
    eleve_id = fields.Int(required=True, error_messages=MESSAGES_ENTIER)
    note = fields.Float(
        required=True,
        validate=validate.Range(min=NOTE_MIN, max=NOTE_MAX, error=_erreur_bornes(NOTE_MIN, NOTE_MAX)),
        error_messages=MESSAGES_NOMBRE,
    )


class ResultatsEcritureSchema(Schema):
    resultats = fields.List(
        fields.Nested(ResultatEntreeSchema),
        required=True,
        validate=validate.Length(min=1, error="La liste resultats ne peut pas être vide."),
        error_messages=MESSAGES_CHAMP,
    )


# ------------------------------------------------------------- Compétence --

class CompetenceSchema(Schema):
    """Valide les types et bornes de base. La cohérence entre
    condition_type et (examen_id, note_min) dépend parfois de l'état déjà
    en base (cas d'un PUT partiel qui ne renvoie que la description, par
    exemple) : cette partie-là reste vérifiée dans la route elle-même,
    après le passage de ce schéma — voir _verifier_coherence_condition
    dans app/routes/competences.py.
    """

    nom = fields.Str(required=True, validate=validate.Length(min=1, max=100), error_messages=MESSAGES_TEXTE)
    categorie = fields.Str(required=True, validate=validate.Length(min=1, max=50), error_messages=MESSAGES_TEXTE)
    description = fields.Str(required=True, validate=validate.Length(min=1, max=500), error_messages=MESSAGES_TEXTE)
    condition_type = fields.Str(
        required=True,
        validate=validate.OneOf(
            [s.value for s in SourceDeblocage],
            error="Valeur invalide : choisir parmi {choices}.",
        ),
        error_messages=MESSAGES_TEXTE,
    )
    examen_id = fields.Int(required=False, allow_none=True, error_messages=MESSAGES_ENTIER)
    note_min = fields.Float(
        required=False,
        allow_none=True,
        validate=validate.Range(min=0, max=20, error=_erreur_bornes(0, 20)),
        error_messages=MESSAGES_NOMBRE,
    )


class CompetenceModificationSchema(CompetenceSchema):
    nom = fields.Str(required=False, validate=validate.Length(min=1, max=100), error_messages=MESSAGES_TEXTE)
    categorie = fields.Str(required=False, validate=validate.Length(min=1, max=50), error_messages=MESSAGES_TEXTE)
    description = fields.Str(required=False, validate=validate.Length(min=1, max=500), error_messages=MESSAGES_TEXTE)
    condition_type = fields.Str(
        required=False,
        validate=validate.OneOf(
            [s.value for s in SourceDeblocage],
            error="Valeur invalide : choisir parmi {choices}.",
        ),
        error_messages=MESSAGES_TEXTE,
    )


# ----------------------------------------------------------------- Tournoi --

class TournoiSchema(Schema):
    nom = fields.Str(required=True, validate=validate.Length(min=1, max=150), error_messages=MESSAGES_TEXTE)
    annee = fields.Int(
        required=True,
        validate=validate.Range(min=2000, max=2100, error=_erreur_bornes(2000, 2100)),
        error_messages=MESSAGES_ENTIER,
    )
    maison_organisatrice_id = fields.Int(required=False, allow_none=True, error_messages=MESSAGES_ENTIER)


# -------------------------------------------------------------------- Duel --

class DuelSchema(Schema):
    eleve_1_id = fields.Int(required=True, error_messages=MESSAGES_ENTIER)
    eleve_2_id = fields.Int(required=True, error_messages=MESSAGES_ENTIER)
    vainqueur_id = fields.Int(required=True, error_messages=MESSAGES_ENTIER)

    @validates_schema
    def _verifier_participants(self, data, **kwargs):
        if data.get("eleve_1_id") == data.get("eleve_2_id"):
            raise ValidationError(
                "eleve_1_id et eleve_2_id doivent être deux élèves différents.",
                field_name="eleve_2_id",
            )
        if data.get("vainqueur_id") not in (data.get("eleve_1_id"), data.get("eleve_2_id")):
            raise ValidationError(
                "vainqueur_id doit être l'un des deux participants.",
                field_name="vainqueur_id",
            )


# -------------------------------------------------------- Année académique --

class AnneeAcademiqueSchema(Schema):
    libelle = fields.Str(required=True, validate=validate.Length(min=1, max=20), error_messages=MESSAGES_TEXTE)
    seuil_promotion = fields.Float(
        required=True,
        validate=validate.Range(min=0, max=20, error=_erreur_bornes(0, 20)),
        error_messages=MESSAGES_NOMBRE,
    )


class AnneeAcademiqueModificationSchema(AnneeAcademiqueSchema):
    libelle = fields.Str(required=False, validate=validate.Length(min=1, max=20), error_messages=MESSAGES_TEXTE)
    seuil_promotion = fields.Float(
        required=False,
        validate=validate.Range(min=0, max=20, error=_erreur_bornes(0, 20)),
        error_messages=MESSAGES_NOMBRE,
    )


# -------------------------------------------------------------- Connexion --

class LoginSchema(Schema):
    """Non branché par défaut sur POST /login (voir app/routes/auth.py) :
    ajouté pour compléter le catalogue de schémas du jour 4, au même
    format que les autres, si vous voulez le brancher vous-même.
    """

    email = fields.Email(required=True, error_messages={**MESSAGES_CHAMP, "invalid": "Doit être une adresse email valide."})
    mot_de_passe = fields.Str(required=True, validate=validate.Length(min=1), error_messages=MESSAGES_TEXTE)


__all__ = [
    "MaisonSchema",
    "ProfesseurSchema",
    "CoursSchema",
    "EleveSchema",
    "InscriptionSchema",
    "ExamenSchema",
    "ExamenModificationSchema",
    "ResultatEntreeSchema",
    "ResultatsEcritureSchema",
    "CompetenceSchema",
    "CompetenceModificationSchema",
    "TournoiSchema",
    "DuelSchema",
    "AnneeAcademiqueSchema",
    "AnneeAcademiqueModificationSchema",
    "LoginSchema",
]

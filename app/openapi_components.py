"""
Schémas de composants OpenAPI : la forme des ressources, des payloads
d'écriture et des réponses métier, réutilisés par $ref depuis les blocs
YAML des docstrings de routes (voir app/openapi_generator.py).

Ces schémas restent ici plutôt que d'être recopiés dans chaque docstring
parce qu'ils sont partagés : Maison, par exemple, est référencée par les
quatre opérations du CRUD (GET liste, GET item, POST, PUT), ça n'aurait
aucun sens de la redéfinir quatre fois. Ce qui est propre à UNE opération
(résumé, description, paramètres, quel code renvoie quoi) vit en
revanche dans la docstring de la route concernée, pas ici.

Historique : ce fichier reprend, sans changement de fond, les schémas de
composants de l'ancien app/openapi_spec.py (jours 1 à 4, dict PATHS tenu à
la main). Seuls les chemins (PATHS) ont changé de méthode de fabrication ;
la forme des ressources elle-même n'a aucune raison de changer avec.
"""

ERREUR_SCHEMA = {
    "type": "object",
    "properties": {"erreur": {"type": "string"}},
    "required": ["erreur"],
}

ERREUR_VALIDATION_SCHEMA = {
    "type": "object",
    "description": (
        "Forme prise par un 400 sur un endpoint d'écriture dont le payload est "
        "invalide (jour 4, voir app/schemas.py et app/validation.py) : `champs` "
        "reprend un message par champ fautif, pas juste un message générique."
    ),
    "properties": {
        "erreur": {"type": "string", "example": "Payload invalide."},
        "champs": {
            "type": "object",
            "additionalProperties": True,
            "example": {
                "annee_etude": ["Doit être compris entre 1 et 7."],
                "maison_id": ["Ce champ est requis."],
            },
        },
    },
    "required": ["erreur", "champs"],
}

MAISON_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "readOnly": True},
        "nom": {"type": "string", "example": "Pyrraxis"},
        "couleur": {"type": "string", "example": "Rouge et or"},
        "fondateur": {"type": "string", "example": "Ignatius Brasier"},
        "valeurs": {"type": "string", "nullable": True, "example": "Courage, audace"},
        "reputation": {
            "type": "integer",
            "readOnly": True,
            "description": "Piloté par la clôture d'un tournoi (jour 3), pas modifiable via l'API.",
        },
    },
}

MAISON_ECRITURE_SCHEMA = {
    "type": "object",
    "properties": {
        "nom": {"type": "string", "example": "Pyrraxis"},
        "couleur": {"type": "string", "example": "Rouge et or"},
        "fondateur": {"type": "string", "example": "Ignatius Brasier"},
        "valeurs": {"type": "string", "example": "Courage, audace"},
    },
    "required": ["nom", "couleur", "fondateur"],
}

PROFESSEUR_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "readOnly": True},
        "nom": {"type": "string", "example": "Théodore Vance"},
        "matiere_enseignee": {"type": "string", "example": "Potions"},
        "anciennete": {"type": "integer", "example": 15},
    },
}

PROFESSEUR_ECRITURE_SCHEMA = {
    "type": "object",
    "properties": {
        "nom": {"type": "string", "example": "Théodore Vance"},
        "matiere_enseignee": {"type": "string", "example": "Potions"},
        "anciennete": {"type": "integer", "example": 15},
    },
    "required": ["nom", "matiere_enseignee", "anciennete"],
}

COURS_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "readOnly": True},
        "intitule": {"type": "string", "example": "Potions avancées"},
        "niveau_requis": {"type": "integer", "example": 4},
        "capacite_max": {"type": "integer", "example": 25},
        "professeur_id": {"type": "integer", "example": 1},
        "annee_academique_id": {
            "type": "integer",
            "readOnly": True,
            "description": "Assigné automatiquement à l'année académique la plus récente en base.",
        },
    },
}

COURS_ECRITURE_SCHEMA = {
    "type": "object",
    "properties": {
        "intitule": {"type": "string", "example": "Potions avancées"},
        "niveau_requis": {"type": "integer", "example": 4},
        "capacite_max": {"type": "integer", "example": 25},
        "professeur_id": {"type": "integer", "example": 1},
    },
    "required": ["intitule", "niveau_requis", "capacite_max", "professeur_id"],
}

ELEVE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "readOnly": True},
        "nom": {"type": "string", "example": "Alaric Corvenoire"},
        "annee_etude": {"type": "integer", "minimum": 1, "maximum": 7, "example": 3},
        "maison_id": {"type": "integer", "example": 1},
        "familier": {"type": "string", "nullable": True, "example": "Chat"},
        "statut": {
            "type": "string",
            "enum": ["actif", "diplome", "renvoye"],
            "example": "actif",
        },
    },
}

ELEVE_ECRITURE_SCHEMA = {
    "type": "object",
    "properties": {
        "nom": {"type": "string", "example": "Alaric Corvenoire"},
        "annee_etude": {"type": "integer", "minimum": 1, "maximum": 7, "example": 3},
        "maison_id": {"type": "integer", "example": 1},
        "familier": {"type": "string", "example": "Chat"},
        "statut": {"type": "string", "enum": ["actif", "diplome", "renvoye"]},
    },
    "required": ["nom", "annee_etude", "maison_id"],
}

LOGIN_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "email": {"type": "string", "format": "email", "example": "admin@academie-sorcellerie.fr"},
        "mot_de_passe": {"type": "string", "example": "admin123"},
    },
    "required": ["email", "mot_de_passe"],
}

IDENTITE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "email": {"type": "string", "format": "email"},
        "role": {"type": "string", "enum": ["eleve", "professeur", "admin"]},
        "eleve_id": {"type": "integer", "nullable": True},
        "professeur_id": {"type": "integer", "nullable": True},
    },
}

# --- Jour 2 --------------------------------------------------------------

INSCRIPTION_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "readOnly": True},
        "eleve_id": {"type": "integer", "example": 1},
        "cours_id": {"type": "integer", "example": 1},
        "date_inscription": {"type": "string", "format": "date"},
        "statut": {
            "type": "string",
            "enum": ["inscrit", "en_cours", "valide", "abandonne"],
            "example": "inscrit",
        },
    },
}

INSCRIPTION_ECRITURE_SCHEMA = {
    "type": "object",
    "properties": {"eleve_id": {"type": "integer", "example": 1}},
    "required": ["eleve_id"],
}

ELEVE_DU_COURS_SCHEMA = {
    "type": "object",
    "properties": {
        "eleve_id": {"type": "integer"},
        "nom": {"type": "string", "example": "Alaric Corvenoire"},
        "maison": {"type": "string", "example": "Pyrraxis"},
        "statut_inscription": {"type": "string", "enum": ["inscrit", "en_cours", "valide", "abandonne"]},
    },
}

EXAMEN_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "readOnly": True},
        "cours_id": {"type": "integer", "example": 1},
        "titre": {"type": "string", "example": "Interrogation 1"},
        "date": {"type": "string", "format": "date", "example": "2026-03-01"},
        "seuil_reussite": {"type": "number", "example": 10},
    },
}

EXAMEN_ECRITURE_SCHEMA = {
    "type": "object",
    "properties": {
        "titre": {"type": "string", "example": "Interrogation 1"},
        "date": {"type": "string", "format": "date", "example": "2026-03-01"},
        "seuil_reussite": {"type": "number", "example": 10},
    },
    "required": ["titre", "date", "seuil_reussite"],
}

RESULTAT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "readOnly": True},
        "eleve_id": {"type": "integer"},
        "examen_id": {"type": "integer"},
        "note": {"type": "number", "minimum": 0, "maximum": 20, "example": 15},
        "statut": {
            "type": "string",
            "enum": ["reussi", "echec"],
            "nullable": True,
            "readOnly": True,
            "description": (
                "Réussite/échec à CET examen, fixée par POST /examens/{id}/cloture. "
                "Vaut null tant que l'examen n'a pas été clôturé, et repasse à null si "
                "la note est réécrite après coup."
            ),
        },
    },
}

RESULTATS_ECRITURE_SCHEMA = {
    "type": "object",
    "description": "Saisie en masse : une entrée par élève, pas un appel par élève.",
    "properties": {
        "resultats": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "eleve_id": {"type": "integer", "example": 1},
                    "note": {"type": "number", "minimum": 0, "maximum": 20, "example": 15},
                },
                "required": ["eleve_id", "note"],
            },
        }
    },
    "required": ["resultats"],
}

CLOTURE_EXAMEN_REPONSE_SCHEMA = {
    "type": "object",
    "description": (
        "Décision réussi/échec par élève pour CET examen uniquement. Ne touche pas "
        "au statut de l'inscription au cours — voir ClotureCoursRapport / "
        "ClotureCoursDecision pour la décision au niveau du cours."
    ),
    "properties": {
        "examen_id": {"type": "integer"},
        "seuil_reussite": {"type": "number"},
        "moyenne_examen": {
            "type": "number",
            "description": "Moyenne de la classe sur cet examen précis.",
        },
        "resultats": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "eleve_id": {"type": "integer"},
                    "note": {"type": "number"},
                    "statut": {"type": "string", "enum": ["reussi", "echec"]},
                },
            },
        },
    },
}

CLOTURE_COURS_RAPPORT_SCHEMA = {
    "type": "object",
    "description": "Réponse en mode rapport (sans ?eleve_id=) : lecture seule, aucune écriture.",
    "properties": {
        "cours_id": {"type": "integer"},
        "intitule": {"type": "string", "example": "Potions avancées"},
        "annee_academique": {"type": "string", "example": "2025-2026"},
        "eleves": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "eleve_id": {"type": "integer"},
                    "nom": {"type": "string"},
                    "moyenne": {
                        "type": "number",
                        "nullable": True,
                        "description": "null si l'élève n'a encore aucun résultat dans le cours.",
                    },
                    "statut": {"type": "string", "enum": ["reussi", "echec"], "nullable": True},
                },
            },
        },
    },
}

CLOTURE_COURS_DECISION_SCHEMA = {
    "type": "object",
    "description": "Réponse en mode décision (avec ?eleve_id=) : met à jour l'inscription de cet élève.",
    "properties": {
        "cours": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "intitule": {"type": "string"},
                "annee_academique": {"type": "string"},
            },
        },
        "eleve": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "nom": {"type": "string"},
                "maison": {"type": "string"},
            },
        },
        "resultats": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "examen_id": {"type": "integer"},
                    "titre_examen": {"type": "string"},
                    "note": {"type": "number"},
                    "statut_examen": {
                        "type": "string",
                        "enum": ["reussi", "echec"],
                        "nullable": True,
                        "description": "Statut de CET examen s'il a déjà été clôturé, sinon null.",
                    },
                },
            },
        },
        "moyenne_cours": {"type": "number"},
        "seuil_retenu": {
            "type": "number",
            "description": "Moyenne des seuil_reussite des examens pris en compte.",
        },
        "decision_finale": {"type": "string", "enum": ["reussi", "echec"]},
        "nouveau_statut_inscription": {"type": "string", "enum": ["en_cours", "valide"]},
    },
}

MOYENNE_COURS_SCHEMA = {
    "type": "object",
    "properties": {
        "cours_id": {"type": "integer"},
        "moyenne": {"type": "number", "nullable": True},
        "nombre_resultats": {"type": "integer"},
    },
}

MON_DOSSIER_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "nom": {"type": "string"},
        "annee_etude": {"type": "integer"},
        "maison": {"type": "string"},
        "familier": {"type": "string", "nullable": True},
        "statut": {"type": "string"},
        "nombre_cours": {"type": "integer"},
        "nombre_notes": {"type": "integer"},
    },
}

# --- Jour 3 --------------------------------------------------------------

COMPETENCE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "readOnly": True},
        "nom": {"type": "string", "example": "Sort de Stupéfixion"},
        "categorie": {"type": "string", "example": "Sorts offensifs"},
        "description": {"type": "string", "example": "Immobilise un adversaire à distance."},
        "condition_type": {"type": "string", "enum": ["examen", "tournoi"]},
        "examen_id": {
            "type": "integer",
            "nullable": True,
            "description": "Rempli seulement si condition_type == 'examen'.",
        },
        "note_min": {
            "type": "number",
            "nullable": True,
            "description": "Note minimale à cet examen pour débloquer la compétence.",
        },
    },
}

COMPETENCE_ECRITURE_SCHEMA = {
    "type": "object",
    "description": (
        "Si condition_type == 'examen', examen_id et note_min sont obligatoires. "
        "Si condition_type == 'tournoi', ils sont ignorés (forcés à null)."
    ),
    "properties": {
        "nom": {"type": "string", "example": "Sort de Stupéfixion"},
        "categorie": {"type": "string", "example": "Sorts offensifs"},
        "description": {"type": "string"},
        "condition_type": {"type": "string", "enum": ["examen", "tournoi"]},
        "examen_id": {"type": "integer", "example": 1},
        "note_min": {"type": "number", "example": 12},
    },
    "required": ["nom", "categorie", "description", "condition_type"],
}

COMPETENCES_PAGE_SCHEMA = {
    "type": "object",
    "description": "Enveloppe de pagination commune aux listings du jour 3.",
    "properties": {
        "elements": {"type": "array", "items": {"$ref": "#/components/schemas/Competence"}},
        "page": {"type": "integer"},
        "par_page": {"type": "integer"},
        "total": {"type": "integer"},
        "pages": {"type": "integer"},
    },
}

TOURNOI_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "readOnly": True},
        "nom": {"type": "string", "example": "Tournoi de printemps"},
        "annee": {"type": "integer", "example": 2026},
        "maison_organisatrice_id": {"type": "integer", "nullable": True},
        "vainqueur_eleve_id": {"type": "integer", "nullable": True, "readOnly": True},
        "cloture_le": {
            "type": "string",
            "format": "date-time",
            "nullable": True,
            "readOnly": True,
            "description": "null tant que le tournoi n'est pas clôturé ; sert de garde anti-rejeu.",
        },
    },
}

TOURNOI_ECRITURE_SCHEMA = {
    "type": "object",
    "properties": {
        "nom": {"type": "string", "example": "Tournoi de printemps"},
        "annee": {"type": "integer", "example": 2026},
        "maison_organisatrice_id": {"type": "integer", "example": 1},
    },
    "required": ["nom", "annee"],
}

TOURNOIS_PAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "elements": {"type": "array", "items": {"$ref": "#/components/schemas/Tournoi"}},
        "page": {"type": "integer"},
        "par_page": {"type": "integer"},
        "total": {"type": "integer"},
        "pages": {"type": "integer"},
    },
}

DUEL_ECRITURE_SCHEMA = {
    "type": "object",
    "description": "Enregistre un duel déjà joué, vainqueur inclus — pas une programmation de duel à venir.",
    "properties": {
        "eleve_1_id": {"type": "integer", "example": 1},
        "eleve_2_id": {"type": "integer", "example": 2},
        "vainqueur_id": {"type": "integer", "example": 1, "description": "Doit être eleve_1_id ou eleve_2_id."},
    },
    "required": ["eleve_1_id", "eleve_2_id", "vainqueur_id"],
}

DUEL_DETAILLE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "eleve_1": {
            "type": "object",
            "properties": {"id": {"type": "integer"}, "nom": {"type": "string"}},
        },
        "eleve_2": {
            "type": "object",
            "properties": {"id": {"type": "integer"}, "nom": {"type": "string"}},
        },
        "vainqueur": {
            "type": "object",
            "nullable": True,
            "properties": {"id": {"type": "integer"}, "nom": {"type": "string"}},
        },
    },
}

CLOTURE_TOURNOI_REPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "tournoi_id": {"type": "integer"},
        "vainqueur_eleve_id": {"type": "integer"},
        "victoires": {"type": "integer"},
        "competences_debloquees": {"type": "array", "items": {"type": "string"}},
        "maison_id": {"type": "integer"},
        "reputation_ajoutee": {"type": "integer"},
        "nouvelle_reputation": {"type": "integer"},
    },
}

EVALUER_COMPETENCES_REPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "examen_id": {"type": "integer"},
        "competences_evaluees": {"type": "array", "items": {"type": "string"}},
        "maitrises_creees": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"eleve_id": {"type": "integer"}, "competence": {"type": "string"}},
            },
        },
        "deja_debloquees": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"eleve_id": {"type": "integer"}, "competence": {"type": "string"}},
            },
        },
    },
}

# --- Jour 4 ----------------------------------------------------------------

ANNEE_ACADEMIQUE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "readOnly": True},
        "libelle": {"type": "string", "example": "2025-2026"},
        "seuil_promotion": {
            "type": "number",
            "example": 10.0,
            "description": "Le \"seuil configurable\" du cahier des charges pour le passage de fin d'année.",
        },
        "cloturee_le": {
            "type": "string",
            "format": "date-time",
            "nullable": True,
            "readOnly": True,
            "description": "null tant que l'année n'est pas clôturée ; sert de garde anti-rejeu.",
        },
    },
}

ANNEE_ACADEMIQUE_ECRITURE_SCHEMA = {
    "type": "object",
    "properties": {
        "libelle": {"type": "string", "example": "2026-2027"},
        "seuil_promotion": {"type": "number", "minimum": 0, "maximum": 20, "example": 10.0},
    },
    "required": ["libelle", "seuil_promotion"],
}

CLOTURE_ANNEE_REPONSE_SCHEMA = {
    "type": "object",
    "description": "Le détail de chaque décision est dans `decisions`, un élément par élève actif traité.",
    "properties": {
        "annee_academique_id": {"type": "integer"},
        "libelle": {"type": "string"},
        "seuil_retenu": {
            "type": "number",
            "description": "seuil_promotion de l'année, sauf si l'appel a fourni ?seuil= en override.",
        },
        "nombre_eleves_actifs": {"type": "integer"},
        "promus": {"type": "integer"},
        "redoublants": {"type": "integer"},
        "diplomes": {"type": "integer"},
        "decisions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "eleve_id": {"type": "integer"},
                    "nom": {"type": "string"},
                    "moyenne_generale": {
                        "type": "number",
                        "nullable": True,
                        "description": "null si l'élève n'a aucune inscription validée cette année (traité comme un redoublement).",
                    },
                    "annee_etude_avant": {"type": "integer"},
                    "annee_etude_apres": {"type": "integer"},
                    "decision": {"type": "string", "enum": ["promu", "redouble", "diplome"]},
                    "statut_apres": {"type": "string", "enum": ["actif", "diplome", "renvoye"]},
                },
            },
        },
    },
}

# Rassemble tout ce qui précède sous les noms utilisés par les $ref des
# docstrings de routes (#/components/schemas/<nom>).
COMPONENTS_SCHEMAS = {
    "Erreur": ERREUR_SCHEMA,
    "ErreurValidation": ERREUR_VALIDATION_SCHEMA,
    "Maison": MAISON_SCHEMA,
    "MaisonEcriture": MAISON_ECRITURE_SCHEMA,
    "Professeur": PROFESSEUR_SCHEMA,
    "ProfesseurEcriture": PROFESSEUR_ECRITURE_SCHEMA,
    "Cours": COURS_SCHEMA,
    "CoursEcriture": COURS_ECRITURE_SCHEMA,
    "Eleve": ELEVE_SCHEMA,
    "EleveEcriture": ELEVE_ECRITURE_SCHEMA,
    "LoginRequest": LOGIN_REQUEST_SCHEMA,
    "Identite": IDENTITE_SCHEMA,
    "Inscription": INSCRIPTION_SCHEMA,
    "InscriptionEcriture": INSCRIPTION_ECRITURE_SCHEMA,
    "EleveDuCours": ELEVE_DU_COURS_SCHEMA,
    "Examen": EXAMEN_SCHEMA,
    "ExamenEcriture": EXAMEN_ECRITURE_SCHEMA,
    "Resultat": RESULTAT_SCHEMA,
    "ResultatsEcriture": RESULTATS_ECRITURE_SCHEMA,
    "ClotureExamenReponse": CLOTURE_EXAMEN_REPONSE_SCHEMA,
    "ClotureCoursRapport": CLOTURE_COURS_RAPPORT_SCHEMA,
    "ClotureCoursDecision": CLOTURE_COURS_DECISION_SCHEMA,
    "MoyenneCours": MOYENNE_COURS_SCHEMA,
    "MonDossier": MON_DOSSIER_SCHEMA,
    "Competence": COMPETENCE_SCHEMA,
    "CompetenceEcriture": COMPETENCE_ECRITURE_SCHEMA,
    "CompetencesPage": COMPETENCES_PAGE_SCHEMA,
    "Tournoi": TOURNOI_SCHEMA,
    "TournoiEcriture": TOURNOI_ECRITURE_SCHEMA,
    "TournoisPage": TOURNOIS_PAGE_SCHEMA,
    "DuelEcriture": DUEL_ECRITURE_SCHEMA,
    "DuelDetaille": DUEL_DETAILLE_SCHEMA,
    "ClotureTournoiReponse": CLOTURE_TOURNOI_REPONSE_SCHEMA,
    "EvaluerCompetencesReponse": EVALUER_COMPETENCES_REPONSE_SCHEMA,
    "AnneeAcademique": ANNEE_ACADEMIQUE_SCHEMA,
    "AnneeAcademiqueEcriture": ANNEE_ACADEMIQUE_ECRITURE_SCHEMA,
    "ClotureAnneeReponse": CLOTURE_ANNEE_REPONSE_SCHEMA,
}

SECURITY_SCHEMES = {
    "XUserId": {
        "type": "apiKey",
        "in": "header",
        "name": "X-User-Id",
        "description": (
            "Connexion simulée du cahier des charges : aucun token, l'id renvoyé "
            "par /login est envoyé tel quel sur les endpoints qui en ont besoin. "
            "Rien ne vérifie l'authenticité de cet id à ce stade du projet."
        ),
    }
}

INFO = {
    "title": "Académie de Sorcellerie — API",
    "version": "1.1.0",
    "description": (
        "API pédagogique du cahier des charges \"Académie de Sorcellerie\", livrée "
        "au complet : jour 1 (modèles, CRUD, connexion simulée), jour 2 "
        "(inscriptions, examens, résultats, clôture d'examen et de cours), jour 3 "
        "(compétences, maîtrises, tournois, duels) et jour 4 (passage de fin "
        "d'année, validation stricte des payloads via marshmallow, seed à volume "
        "réaliste). À partir de la version 1.1.0, cette spec n'est plus tenue à la "
        "main : elle est reconstruite à chaque démarrage à partir des docstrings "
        "des routes (voir app/openapi_generator.py)."
    ),
}

SERVERS = [{"url": "/", "description": "Serveur de développement local"}]

TAGS = [
    {"name": "Diagnostic"},
    {"name": "Authentification", "description": "Connexion simulée : POST /login puis header X-User-Id."},
    {"name": "Maisons"},
    {"name": "Professeurs"},
    {"name": "Cours"},
    {"name": "Eleves"},
    {"name": "Inscriptions"},
    {"name": "Examens"},
    {"name": "Résultats"},
    {"name": "Compétences", "description": "Catalogue et déblocage automatique (jour 3)."},
    {"name": "Tournois", "description": "Tournois, duels et clôture (jour 3)."},
    {"name": "Espace élève", "description": "Endpoints scopés sur l'élève résolu via X-User-Id."},
    {"name": "Passage d'année", "description": "Année académique et clôture de fin d'année (jour 4)."},
]

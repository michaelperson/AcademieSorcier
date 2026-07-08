"""
Spec OpenAPI écrite à la main plutôt que générée à partir des routes : à ce
stade du projet (pas encore de marshmallow/pydantic, cf. jour 4), il n'y a
rien à introspecter automatiquement. Un dict Python reste simple à faire
évoluer au fil des jours suivants, sans dépendance supplémentaire dans
requirements.txt.

Servie telle quelle en JSON sur /openapi.json (voir app/routes/docs.py),
et lue par Scalar sur /docs pour l'interface de documentation interactive.
"""

ERREUR_SCHEMA = {
    "type": "object",
    "properties": {"erreur": {"type": "string"}},
    "required": ["erreur"],
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


def _reponse_erreur(description):
    return {
        "description": description,
        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Erreur"}}},
    }


def _crud_paths(nom_ressource, tag, schema_lecture, schema_ecriture, exemple_id=1):
    """Fabrique les deux chemins REST standards (collection + item) pour
    une ressource au CRUD symétrique (Maison, Professeur, Cours, Eleve).
    """
    base = f"/{nom_ressource}"
    item = f"/{nom_ressource}/{{id}}"

    return {
        base: {
            "get": {
                "tags": [tag],
                "summary": f"Lister les {tag.lower()}",
                "responses": {
                    "200": {
                        "description": "Liste des ressources.",
                        "content": {
                            "application/json": {
                                "schema": {"type": "array", "items": schema_lecture}
                            }
                        },
                    }
                },
            },
            "post": {
                "tags": [tag],
                "summary": f"Créer un(e) {tag.lower()[:-1] if tag.endswith('s') else tag.lower()}",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": schema_ecriture}},
                },
                "responses": {
                    "201": {
                        "description": "Ressource créée.",
                        "content": {"application/json": {"schema": schema_lecture}},
                    },
                    "400": _reponse_erreur("Payload invalide (champ manquant ou référence introuvable)."),
                },
            },
        },
        item: {
            "parameters": [
                {
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "integer"},
                    "example": exemple_id,
                }
            ],
            "get": {
                "tags": [tag],
                "summary": "Obtenir une ressource par id",
                "responses": {
                    "200": {
                        "description": "Ressource trouvée.",
                        "content": {"application/json": {"schema": schema_lecture}},
                    },
                    "404": _reponse_erreur("Ressource introuvable."),
                },
            },
            "put": {
                "tags": [tag],
                "summary": "Modifier une ressource",
                "requestBody": {
                    "required": True,
                    "content": {"application/json": {"schema": schema_ecriture}},
                },
                "responses": {
                    "200": {
                        "description": "Ressource modifiée.",
                        "content": {"application/json": {"schema": schema_lecture}},
                    },
                    "400": _reponse_erreur("Payload invalide."),
                    "404": _reponse_erreur("Ressource introuvable."),
                },
            },
            "delete": {
                "tags": [tag],
                "summary": "Supprimer une ressource",
                "responses": {
                    "200": {"description": "Ressource supprimée."},
                    "404": _reponse_erreur("Ressource introuvable."),
                },
            },
        },
    }


PATHS = {
    "/health": {
        "get": {
            "tags": ["Diagnostic"],
            "summary": "Vérifier que l'API répond",
            "responses": {"200": {"description": "L'API est en ligne."}},
        }
    },
    "/login": {
        "post": {
            "tags": ["Authentification"],
            "summary": "Connexion simulée",
            "description": (
                "Vérifie email + mot de passe (comparaison en clair, temporaire — voir "
                "app/routes/auth.py). Renvoie l'identité et l'id à utiliser ensuite dans "
                "le header X-User-Id."
            ),
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {"schema": {"$ref": "#/components/schemas/LoginRequest"}}
                },
            },
            "responses": {
                "200": {
                    "description": "Connexion réussie.",
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/Identite"}}
                    },
                },
                "400": _reponse_erreur("email ou mot_de_passe manquant."),
                "401": _reponse_erreur("Email ou mot de passe incorrect."),
            },
        }
    },
    "/whoami": {
        "get": {
            "tags": ["Authentification"],
            "summary": "Identité résolue à partir du header X-User-Id",
            "security": [{"XUserId": []}],
            "responses": {
                "200": {
                    "description": "Identité de l'utilisateur du header.",
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/Identite"}}
                    },
                },
                "401": _reponse_erreur(
                    "Header X-User-Id manquant, invalide, ou ne correspondant à personne."
                ),
            },
        }
    },
    "/cours/{id}/inscriptions": {
        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
        "post": {
            "tags": ["Inscriptions"],
            "summary": "Inscrire un élève à ce cours",
            "description": "Refusé si le cours a atteint sa capacité maximale ou si l'élève y est déjà inscrit.",
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {"schema": {"$ref": "#/components/schemas/InscriptionEcriture"}}
                },
            },
            "responses": {
                "201": {
                    "description": "Inscription créée.",
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/Inscription"}}
                    },
                },
                "400": _reponse_erreur("Cours complet, élève déjà inscrit, ou élève introuvable."),
                "404": _reponse_erreur("Cours introuvable."),
            },
        },
    },
    "/cours/{id}/eleves": {
        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
        "get": {
            "tags": ["Inscriptions"],
            "summary": "Lister les élèves inscrits à ce cours",
            "description": (
                "Endpoint utilisé pour la chasse au N+1 (voir PERFORMANCE.md). "
                "`?eager=true` active joinedload sur eleve + maison."
            ),
            "parameters": [
                {
                    "name": "eager",
                    "in": "query",
                    "schema": {"type": "boolean", "default": False},
                    "description": "Active le chargement anticipé (joinedload) au lieu du chargement paresseux.",
                }
            ],
            "responses": {
                "200": {
                    "description": "Liste des élèves du cours.",
                    "content": {
                        "application/json": {
                            "schema": {"type": "array", "items": {"$ref": "#/components/schemas/EleveDuCours"}}
                        }
                    },
                },
                "404": _reponse_erreur("Cours introuvable."),
            },
        },
    },
    "/cours/{id}/examens": {
        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
        "get": {
            "tags": ["Examens"],
            "summary": "Lister les examens de ce cours",
            "responses": {
                "200": {
                    "description": "Liste des examens.",
                    "content": {
                        "application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Examen"}}}
                    },
                },
                "404": _reponse_erreur("Cours introuvable."),
            },
        },
        "post": {
            "tags": ["Examens"],
            "summary": "Créer un examen pour ce cours",
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ExamenEcriture"}}},
            },
            "responses": {
                "201": {
                    "description": "Examen créé.",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Examen"}}},
                },
                "400": _reponse_erreur("Payload invalide."),
                "404": _reponse_erreur("Cours introuvable."),
            },
        },
    },
    "/examens/{id}": {
        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
        "get": {
            "tags": ["Examens"],
            "summary": "Obtenir un examen",
            "responses": {
                "200": {"description": "Examen trouvé.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Examen"}}}},
                "404": _reponse_erreur("Examen introuvable."),
            },
        },
        "put": {
            "tags": ["Examens"],
            "summary": "Modifier un examen",
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ExamenEcriture"}}},
            },
            "responses": {
                "200": {"description": "Examen modifié.", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Examen"}}}},
                "400": _reponse_erreur("Payload invalide."),
                "404": _reponse_erreur("Examen introuvable."),
            },
        },
        "delete": {
            "tags": ["Examens"],
            "summary": "Supprimer un examen",
            "responses": {
                "200": {"description": "Examen supprimé."},
                "404": _reponse_erreur("Examen introuvable."),
            },
        },
    },
    "/examens/{id}/resultats": {
        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
        "get": {
            "tags": ["Résultats"],
            "summary": "Lister les résultats de cet examen",
            "responses": {
                "200": {
                    "description": "Liste des résultats.",
                    "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Resultat"}}}},
                },
                "404": _reponse_erreur("Examen introuvable."),
            },
        },
        "post": {
            "tags": ["Résultats"],
            "summary": "Saisir les résultats de cet examen en masse",
            "description": (
                "Validation atomique : si une seule entrée du payload est invalide "
                "(élève non inscrit au cours, note hors bornes...), rien n'est écrit en base. "
                "Réécrire la note d'un élève déjà noté efface son statut réussi/échec "
                "précédent (il faut reclôturer l'examen pour le refixer)."
            ),
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ResultatsEcriture"}}},
            },
            "responses": {
                "201": {
                    "description": "Résultats enregistrés.",
                    "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Resultat"}}}},
                },
                "400": _reponse_erreur("Payload invalide (voir le détail par entrée dans la réponse)."),
                "404": _reponse_erreur("Examen introuvable."),
            },
        },
    },
    "/examens/{id}/cloture": {
        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
        "post": {
            "tags": ["Examens"],
            "summary": "Clôturer un examen (réussi/échec par examen)",
            "description": (
                "Décide, pour chaque élève ayant un résultat à cet examen, s'il l'a "
                "réussi ou échoué — jugement propre à CET examen, écrit sur le statut du "
                "résultat (Resultat.statut). Ne met PAS à jour le statut de l'inscription "
                "au cours : cette décision-là, basée sur la moyenne de tous les examens du "
                "cours, se fait via POST /cours/{id}/cloture. Refusé (400) tant qu'un "
                "élève du cours n'a pas de résultat pour cet examen. Idempotent."
            ),
            "responses": {
                "200": {
                    "description": "Clôture effectuée.",
                    "content": {
                        "application/json": {"schema": {"$ref": "#/components/schemas/ClotureExamenReponse"}}
                    },
                },
                "400": _reponse_erreur(
                    "Aucun résultat saisi pour cet examen, ou résultats manquants pour "
                    "un ou plusieurs élèves du cours."
                ),
                "404": _reponse_erreur("Examen introuvable."),
            },
        },
    },
    "/cours/{id}/cloture": {
        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
        "post": {
            "tags": ["Cours"],
            "summary": "Clôturer un cours (moyenne générale, statut d'inscription)",
            "description": (
                "Calcule la moyenne des examens passés par un élève dans ce cours, et en "
                "tire la décision qui met à jour Inscription.statut — contrairement à la "
                "clôture d'un examen, qui ne juge que cet examen-là (voir "
                "/examens/{id}/cloture). Deux modes selon le paramètre `eleve_id` : sans, "
                "un rapport en lecture seule sur toute la classe ; avec, la mise à jour "
                "de l'inscription de cet élève précis, et lui seul."
            ),
            "parameters": [
                {
                    "name": "eleve_id",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "integer"},
                    "description": (
                        "Absent : mode rapport (tous les élèves, aucune écriture). "
                        "Présent : met à jour l'inscription de cet élève uniquement."
                    ),
                }
            ],
            "responses": {
                "200": {
                    "description": "Rapport (sans eleve_id) ou décision (avec eleve_id).",
                    "content": {
                        "application/json": {
                            "schema": {
                                "oneOf": [
                                    {"$ref": "#/components/schemas/ClotureCoursRapport"},
                                    {"$ref": "#/components/schemas/ClotureCoursDecision"},
                                ]
                            }
                        }
                    },
                },
                "400": _reponse_erreur(
                    "eleve_id non numérique, ou élève sans aucun résultat dans ce cours."
                ),
                "404": _reponse_erreur("Cours introuvable, ou élève non inscrit à ce cours."),
            },
        },
    },
    "/resultats": {
        "get": {
            "tags": ["Résultats"],
            "summary": "Lister les résultats, filtrable par cours et/ou par examen",
            "parameters": [
                {"name": "cours_id", "in": "query", "schema": {"type": "integer"}},
                {"name": "examen_id", "in": "query", "schema": {"type": "integer"}},
            ],
            "responses": {
                "200": {
                    "description": "Liste des résultats correspondant aux filtres.",
                    "content": {"application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/Resultat"}}}},
                }
            },
        }
    },
    "/cours/{id}/moyenne": {
        "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
        "get": {
            "tags": ["Résultats"],
            "summary": "Moyenne de tous les résultats du cours",
            "responses": {
                "200": {
                    "description": "Moyenne calculée.",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MoyenneCours"}}},
                },
                "404": _reponse_erreur("Cours introuvable."),
            },
        },
    },
    "/moi/cours": {
        "get": {
            "tags": ["Espace élève"],
            "summary": "Mes cours",
            "security": [{"XUserId": []}],
            "responses": {
                "200": {"description": "Cours de l'élève courant."},
                "401": _reponse_erreur("Header X-User-Id manquant ou invalide."),
                "403": _reponse_erreur("L'utilisateur résolu n'a pas le rôle élève."),
            },
        }
    },
    "/moi/notes": {
        "get": {
            "tags": ["Espace élève"],
            "summary": "Mes notes",
            "security": [{"XUserId": []}],
            "responses": {
                "200": {"description": "Résultats de l'élève courant, avec le statut réussi/échec par examen s'il est connu."},
                "401": _reponse_erreur("Header X-User-Id manquant ou invalide."),
                "403": _reponse_erreur("L'utilisateur résolu n'a pas le rôle élève."),
            },
        }
    },
    "/moi/dossier": {
        "get": {
            "tags": ["Espace élève"],
            "summary": "Mon dossier",
            "security": [{"XUserId": []}],
            "responses": {
                "200": {
                    "description": "Dossier de l'élève courant.",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MonDossier"}}},
                },
                "401": _reponse_erreur("Header X-User-Id manquant ou invalide."),
                "403": _reponse_erreur("L'utilisateur résolu n'a pas le rôle élève."),
            },
        }
    },
}

PATHS.update(_crud_paths("maisons", "Maisons", MAISON_SCHEMA, MAISON_ECRITURE_SCHEMA))
PATHS.update(_crud_paths("professeurs", "Professeurs", PROFESSEUR_SCHEMA, PROFESSEUR_ECRITURE_SCHEMA))
PATHS.update(_crud_paths("cours", "Cours", COURS_SCHEMA, COURS_ECRITURE_SCHEMA))
PATHS.update(_crud_paths("eleves", "Eleves", ELEVE_SCHEMA, ELEVE_ECRITURE_SCHEMA))


OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "Académie de Sorcellerie — API",
        "version": "0.4.0",
        "description": (
            "API pédagogique du cahier des charges \"Académie de Sorcellerie\". "
            "Jour 1 (modèles, CRUD, connexion simulée) et jour 2 (inscriptions, "
            "examens, résultats, clôture d'examen et clôture de cours) livrés. "
            "Jour 3 (compétences, tournois) à venir."
        ),
    },
    "servers": [{"url": "/", "description": "Serveur de développement local"}],
    "tags": [
        {"name": "Diagnostic"},
        {"name": "Authentification", "description": "Connexion simulée : POST /login puis header X-User-Id."},
        {"name": "Maisons"},
        {"name": "Professeurs"},
        {"name": "Cours"},
        {"name": "Eleves"},
        {"name": "Inscriptions"},
        {"name": "Examens"},
        {"name": "Résultats"},
        {"name": "Espace élève", "description": "Endpoints scopés sur l'élève résolu via X-User-Id."},
    ],
    "paths": PATHS,
    "components": {
        "schemas": {
            "Erreur": ERREUR_SCHEMA,
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
        },
        "securitySchemes": {
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
        },
    },
}

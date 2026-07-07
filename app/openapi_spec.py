"""
Spec OpenAPI écrite à la main plutôt que générée à partir des routes : à ce
stade du projet (pas encore de marshmallow/pydantic, cf. jour 4), il n'y a
rien à introspecter automatiquement. Un dict Python reste simple à faire
évoluer au fil des jours suivants, sans dépendance supplémentaire dans
requirements.txt. À terme, si vous ajoutez une lib de validation de schéma,
il est courant qu'elle sache générer cette spec toute seule — mais rien
n'oblige à migrer.

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
}

PATHS.update(_crud_paths("maisons", "Maisons", MAISON_SCHEMA, MAISON_ECRITURE_SCHEMA))
PATHS.update(_crud_paths("professeurs", "Professeurs", PROFESSEUR_SCHEMA, PROFESSEUR_ECRITURE_SCHEMA))
PATHS.update(_crud_paths("cours", "Cours", COURS_SCHEMA, COURS_ECRITURE_SCHEMA))
PATHS.update(_crud_paths("eleves", "Eleves", ELEVE_SCHEMA, ELEVE_ECRITURE_SCHEMA))


OPENAPI_SPEC = {
    "openapi": "3.1.0",
    "info": {
        "title": "Académie de Sorcellerie — API",
        "version": "0.2.0",
        "description": (
            "API pédagogique du cahier des charges \"Académie de Sorcellerie\". "
            "Cette spec suit l'avancement réel du projet : jour 1 (modèles, CRUD, "
            "connexion simulée) livré, jour 2 (inscriptions, examens) à venir."
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

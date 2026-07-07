"""
Connexion simulée : aucun token, aucune session — chaque requête porte un
header X-User-Id que ce module lit et résout en Utilisateur. Comme le
précise le cahier des charges, rien ici ne vérifie que la personne qui
envoie ce header est bien qui elle prétend être ; c'est un choix de
périmètre du projet (la sécurité réelle est hors scope), pas un oubli.
"""

from functools import wraps

from flask import g, jsonify, request

from app.extensions import db
from app.models import Utilisateur


def resoudre_utilisateur_courant():
    """Lit X-User-Id sur la requête courante et retourne (utilisateur, None)
    si tout va bien, ou (None, (message, code_http)) sinon. Ne lève jamais
    d'exception : c'est aux décorateurs ci-dessous de décider quoi faire du
    résultat.
    """
    valeur_header = request.headers.get("X-User-Id")
    if valeur_header is None:
        return None, ("Header X-User-Id manquant.", 401)

    try:
        user_id = int(valeur_header)
    except ValueError:
        return None, ("Header X-User-Id invalide : doit être un identifiant entier.", 401)

    utilisateur = db.session.get(Utilisateur, user_id)
    if utilisateur is None:
        return None, (f"Aucun utilisateur avec l'id {user_id}.", 401)

    return utilisateur, None


def connexion_requise(vue):
    """Exige un header X-User-Id valide, pose flask.g.utilisateur_courant
    pour la vue décorée. N'impose aucun rôle particulier — voir
    role_requis() pour restreindre à l'espace admin ou élève.
    """

    @wraps(vue)
    def wrapper(*args, **kwargs):
        utilisateur, erreur = resoudre_utilisateur_courant()
        if erreur is not None:
            message, code = erreur
            return jsonify({"erreur": message}), code

        g.utilisateur_courant = utilisateur
        return vue(*args, **kwargs)

    return wrapper


def role_requis(*roles_autorises):
    """Comme connexion_requise, mais renvoie 403 si le rôle de
    l'utilisateur résolu n'est pas dans roles_autorises.

    Usage :
        @role_requis(RoleUtilisateur.ADMIN)
        def creer_maison(): ...
    """

    def decorateur(vue):
        @wraps(vue)
        def wrapper(*args, **kwargs):
            utilisateur, erreur = resoudre_utilisateur_courant()
            if erreur is not None:
                message, code = erreur
                return jsonify({"erreur": message}), code

            if utilisateur.role not in roles_autorises:
                return jsonify({"erreur": "Accès refusé pour ce rôle."}), 403

            g.utilisateur_courant = utilisateur
            return vue(*args, **kwargs)

        return wrapper

    return decorateur

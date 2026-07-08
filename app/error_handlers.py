"""
Gestion centralisée des exceptions : un seul endroit qui décide de la
réponse JSON renvoyée pour tout ce qui remonte jusqu'ici, plutôt que de
laisser chaque route se débrouiller — ou pire, laisser Flask renvoyer une
page HTML pour une 404/405 alors que le reste de l'API ne répond qu'en
JSON.

Flask n'a pas de middleware d'exception au sens Express ou Django ;
app.errorhandler(...) en est l'équivalent : il route vers le bon
gestionnaire selon le type d'exception, du plus spécifique au plus général
(Flask regarde la hiérarchie des classes, pas l'ordre d'enregistrement).
Trois niveaux, du plus spécifique au plus large :

1. HTTPException — erreurs propres à Flask/Werkzeug (route inconnue,
   méthode non supportée...).
2. SQLAlchemyError — tout ce qui vient de la couche base de données.
3. Exception — filet de sécurité pour tout le reste (un bug, un appel qui
   plante ailleurs...).

Ce mécanisme ne remplace PAS les validations déjà faites route par route
(champ manquant, cours complet, etc.) : celles-ci restent les mieux
placées pour produire un message précis et un bon code 400. Il couvre ce
qu'aucune route ne peut anticiper.
"""

from flask import current_app, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app.extensions import db

MESSAGE_ERREUR_GENERIQUE = "Une erreur interne est survenue."
MESSAGE_ERREUR_BASE_DE_DONNEES = (
    "Erreur de base de données. Consultez les logs du serveur pour le détail."
)

# Un mot de plus que la description brute de Werkzeug, sur les codes qu'on
# a le plus de chances de croiser, pour rester dans le même ton que le
# reste de l'API. Les codes non listés gardent la description de Werkzeug.
MESSAGES_HTTP_PAR_DEFAUT = {
    400: "Requête invalide.",
    404: "Ressource introuvable.",
    405: "Méthode non autorisée sur cette URL.",
}


def enregistrer_gestionnaires_erreurs(app):
    @app.errorhandler(HTTPException)
    def gerer_erreur_http(erreur: HTTPException):
        message = MESSAGES_HTTP_PAR_DEFAUT.get(erreur.code, erreur.description)
        return jsonify({"erreur": message}), erreur.code

    @app.errorhandler(SQLAlchemyError)
    def gerer_erreur_base_de_donnees(erreur: SQLAlchemyError):
        """Le rollback n'est pas optionnel : une session dont la
        transaction a échoué reste inutilisable pour la requête suivante
        tant qu'elle n'est pas explicitement annulée (le symptôme typique,
        sans ce rollback, est une deuxième erreur sans rapport avec la
        première sur la requête d'après).
        """
        db.session.rollback()
        current_app.logger.exception(
            "Erreur base de données sur %s %s", request.method, request.path
        )
        return jsonify({"erreur": MESSAGE_ERREUR_BASE_DE_DONNEES}), 500

    @app.errorhandler(Exception)
    def gerer_exception_inattendue(erreur: Exception):
        """La trace complète part dans les logs, pas dans la réponse : un
        client de l'API n'a rien à faire d'une trace Python, et l'exposer
        est une fuite d'information (chemins de fichiers, requêtes SQL...).
        """
        current_app.logger.exception(
            "Exception non gérée sur %s %s", request.method, request.path
        )
        return jsonify({"erreur": MESSAGE_ERREUR_GENERIQUE}), 500

    return app

import os

from flask import Flask

from app.extensions import db


def create_app(config_name=None):
    """App factory : construit et retourne une instance Flask configurée.

    L'app factory permet de créer plusieurs instances de l'application avec
    des configurations différentes (développement, tests) sans se marcher
    dessus — c'est notamment ce qui permet aux tests de tourner sur une base
    en mémoire pendant que le serveur de développement utilise le fichier
    SQLite du disque.
    """
    from config import CONFIG_BY_NAME

    config_name = config_name or os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(CONFIG_BY_NAME[config_name])

    db.init_app(app)

    # Enregistre toutes les entités sur la metadata de db.Model : sans cet
    # import, db.create_all() ne créerait aucune table (rien ne les lui
    # aurait présentées), et les relationship() en chaîne de caractères
    # d'un module à l'autre ne se résoudraient pas.
    from app import models  # noqa: F401

    from app.error_handlers import enregistrer_gestionnaires_erreurs
    from app.logging_config import configurer_logging

    configurer_logging(app)
    enregistrer_gestionnaires_erreurs(app)

    register_blueprints(app)

    return app


def register_blueprints(app):
    from app.routes.auth import auth_bp
    from app.routes.cours import cours_bp
    from app.routes.docs import docs_bp
    from app.routes.eleves import eleves_bp
    from app.routes.espace_eleve import espace_eleve_bp
    from app.routes.examens import examens_bp
    from app.routes.health import health_bp
    from app.routes.inscriptions import inscriptions_bp
    from app.routes.maisons import maisons_bp
    from app.routes.professeurs import professeurs_bp
    from app.routes.resultats import resultats_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(docs_bp)
    app.register_blueprint(maisons_bp)
    app.register_blueprint(professeurs_bp)
    app.register_blueprint(cours_bp)
    app.register_blueprint(eleves_bp)
    app.register_blueprint(inscriptions_bp)
    app.register_blueprint(examens_bp)
    app.register_blueprint(resultats_bp)
    app.register_blueprint(espace_eleve_bp)

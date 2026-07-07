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

    register_blueprints(app)

    return app


def register_blueprints(app):
    from app.routes.health import health_bp

    app.register_blueprint(health_bp)

    # Enregistrez ici les blueprints des ressources au fur et à mesure
    # qu'elles apparaissent : maisons, professeurs, cours, eleves, auth...
    # from app.routes.maisons import maisons_bp
    # app.register_blueprint(maisons_bp)

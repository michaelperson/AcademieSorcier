"""
Configuration du logging applicatif : format commun, niveau piloté par
config, et un journal d'accès (méthode, chemin, code retour, durée) pour
chaque requête.

Flask n'a pas de vraie chaîne de middlewares comme Express ou Django ; les
hooks before_request/after_request en tiennent lieu ici pour le journal
d'accès, de la même façon que app/error_handlers.py s'appuie sur
app.errorhandler(...) pour la gestion centralisée des exceptions.
"""

import logging
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import g, request

NOM_LOGGER_ACCES = "app.access"


def configurer_logging(app):
    """Prépare app.logger (utilisé partout, y compris par
    app/error_handlers.py) et un logger séparé pour le journal d'accès —
    séparé pour ne pas mélanger une ligne "erreur avec traceback" et une
    ligne "requête traitée normalement" dans le même flux au même niveau.
    """
    niveau = getattr(logging, str(app.config.get("LOG_LEVEL", "INFO")).upper(), logging.INFO)
    formateur = logging.Formatter(
        fmt="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Le rechargeur automatique de Flask (debug=True) importe l'application
    # une seconde fois dans un sous-processus : sans ce garde-fou, chaque
    # ligne de log s'afficherait en double après le premier rechargement.
    if not app.logger.handlers:
        handler_console = logging.StreamHandler()
        handler_console.setFormatter(formateur)
        app.logger.addHandler(handler_console)

        if app.config.get("LOG_TO_FILE"):
            dossier_logs = Path(app.root_path).parent / "logs"
            dossier_logs.mkdir(exist_ok=True)
            handler_fichier = RotatingFileHandler(
                dossier_logs / "app.log",
                maxBytes=1_000_000,
                backupCount=3,
                encoding="utf-8",
            )
            handler_fichier.setFormatter(formateur)
            app.logger.addHandler(handler_fichier)

    app.logger.setLevel(niveau)

    logger_acces = logging.getLogger(NOM_LOGGER_ACCES)
    logger_acces.setLevel(niveau)
    logger_acces.handlers = list(app.logger.handlers)
    # Sans ce False, la ligne remonterait aussi au logger racine et
    # s'afficherait une seconde fois si un autre outil configure celui-ci.
    logger_acces.propagate = False

    @app.before_request
    def _marquer_debut_requete():
        g.debut_requete = time.perf_counter()

    @app.after_request
    def _journaliser_requete(reponse):
        debut = g.get("debut_requete", None)
        duree_ms = (time.perf_counter() - debut) * 1000 if debut is not None else 0.0
        logger_acces.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.path,
            reponse.status_code,
            duree_ms,
        )
        return reponse

    return app

"""
Instances d'extensions partagées, créées une seule fois ici puis attachées
à l'application dans create_app() via .init_app(app).

Ce découplage évite les imports circulaires : les modules de app/models
peuvent importer `db` depuis ce fichier sans jamais avoir besoin d'importer
app/__init__.py.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

"""
Placez ici un module par entité (maison.py, professeur.py, eleve.py, ...) et
importez chaque modèle dans ce fichier, pour que db.create_all() et Alembic
(si vous l'ajoutez plus tard) les découvrent tous en important simplement
`app.models`.

Exemple :
    from app.models.maison import Maison
    from app.models.professeur import Professeur
"""

from datetime import datetime

from app.extensions import db


class TimestampMixin:
    """Mixin à ajouter à vos modèles pour obtenir created_at / updated_at
    sans les redéclarer sur chaque entité (utile dès le jour 1, imposé par
    le cahier des charges au jour 4).

    Usage :
        class Maison(db.Model, TimestampMixin):
            ...
    """

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

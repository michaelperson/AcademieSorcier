"""
Point d'entrée du script de seed : `python seed.py`.

Rien n'est peuplé pour l'instant, ce sera le travail du jour 1. Gardez à
l'esprit dès la première version le critère du jour 4 : le script doit
rester rejouable sans dupliquer ni casser les données (vérifiez l'existence
avant de créer, ou videz les tables concernées en début de script).
"""

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    db.create_all()

    # TODO jour 1 : créer les maisons, professeurs, cours, élèves et
    # utilisateurs de test décrits dans le cahier des charges.

    db.session.commit()
    print("Base initialisée. Seed à compléter (voir TODO dans seed.py).")

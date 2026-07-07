import pytest

from app import create_app
from app.extensions import db
from app.models import AnneeAcademique, Eleve, Maison, Professeur, Utilisateur
from app.models.enums import RoleUtilisateur


@pytest.fixture
def app():
    """Une instance d'application par test, sur une base SQLite en mémoire."""
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def annee_academique(app):
    annee = AnneeAcademique(libelle="2025-2026", seuil_promotion=10.0)
    db.session.add(annee)
    db.session.commit()
    return annee


@pytest.fixture
def maison(app):
    maison = Maison(nom="Pyrraxis", couleur="Rouge et or", fondateur="Ignatius Brasier")
    db.session.add(maison)
    db.session.commit()
    return maison


@pytest.fixture
def professeur(app):
    professeur = Professeur(nom="Théodore Vance", matiere_enseignee="Potions", anciennete=15)
    db.session.add(professeur)
    db.session.commit()
    return professeur


@pytest.fixture
def eleve(app, maison):
    eleve = Eleve(nom="Alaric Corvenoire", annee_etude=3, maison_id=maison.id)
    db.session.add(eleve)
    db.session.commit()
    return eleve


@pytest.fixture
def utilisateur_admin(app):
    admin = Utilisateur(
        email="admin@academie-sorcellerie.fr",
        mot_de_passe="admin123",
        role=RoleUtilisateur.ADMIN,
    )
    db.session.add(admin)
    db.session.commit()
    return admin


@pytest.fixture
def utilisateur_eleve(app, eleve):
    utilisateur = Utilisateur(
        email="alaric.corvenoire@academie-sorcellerie.fr",
        mot_de_passe="motdepasse123",
        role=RoleUtilisateur.ELEVE,
        eleve_id=eleve.id,
    )
    db.session.add(utilisateur)
    db.session.commit()
    return utilisateur

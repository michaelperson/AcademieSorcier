import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    """Une instance d'application par test, sur une base SQLite en mémoire.

    Ajoutez ici vos futures fixtures de données (une maison de test, un
    élève de test, ...) une fois les modèles écrits.
    """
    app = create_app("testing")

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()

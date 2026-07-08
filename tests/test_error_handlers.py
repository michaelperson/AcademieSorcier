"""
Vérifie que la gestion d'erreurs centralisée (app/error_handlers.py)
s'applique bien à des cas qu'aucune route n'anticipe elle-même :
route inconnue, méthode non supportée, panne base de données, bug
imprévu. Les erreurs métier (400 sur un payload invalide, 404 sur une
ressource absente) sont déjà couvertes par les autres fichiers de tests,
route par route — ce n'est pas leur rôle ici.
"""

import logging

from sqlalchemy.exc import OperationalError

from app.extensions import db


def test_route_inconnue_renvoie_du_json_pas_du_html(client):
    reponse = client.get("/cette-route-n-existe-pas")
    assert reponse.status_code == 404
    assert reponse.is_json
    assert reponse.get_json() == {"erreur": "Ressource introuvable."}


def test_methode_non_autorisee_renvoie_du_json(client):
    reponse = client.delete("/health")
    assert reponse.status_code == 405
    assert reponse.is_json
    assert "erreur" in reponse.get_json()


def test_exception_inattendue_renvoie_une_reponse_generique_sans_fuite(client, monkeypatch):
    def _lever_une_erreur(*args, **kwargs):
        raise RuntimeError("panne simulée pour le test — ne doit jamais apparaître au client")

    monkeypatch.setattr(db.session, "query", _lever_une_erreur)

    reponse = client.get("/maisons")
    assert reponse.status_code == 500
    corps = reponse.get_json()
    assert corps == {"erreur": "Une erreur interne est survenue."}
    assert "panne simulée" not in reponse.get_data(as_text=True)


def test_erreur_sqlalchemy_declenche_un_rollback_et_reste_en_json(client, monkeypatch):
    appele = {"rollback": False}

    def _lever_une_erreur_sql(*args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("no such table: maison"))

    def _rollback_espion():
        appele["rollback"] = True

    monkeypatch.setattr(db.session, "query", _lever_une_erreur_sql)
    monkeypatch.setattr(db.session, "rollback", _rollback_espion)

    reponse = client.get("/maisons")
    assert reponse.status_code == 500
    assert reponse.get_json() == {
        "erreur": "Erreur de base de données. Consultez les logs du serveur pour le détail."
    }
    assert appele["rollback"] is True


def test_chaque_requete_est_journalisee(client, caplog):
    """logger_acces a propagate=False (voir app/logging_config.py, pour ne
    pas journaliser deux fois la même ligne en remontant vers app.logger,
    qui porte les mêmes handlers) : caplog, qui écoute sur le logger
    racine, ne verrait donc rien sans qu'on lui attache explicitement son
    handler sur "app.access".
    """
    logger_acces = logging.getLogger("app.access")
    logger_acces.addHandler(caplog.handler)
    try:
        with caplog.at_level("INFO", logger="app.access"):
            client.get("/health")
    finally:
        logger_acces.removeHandler(caplog.handler)

    lignes = [m for m in caplog.messages if "GET" in m and "/health" in m]
    assert lignes, "aucune ligne de journal d'accès trouvée pour GET /health"

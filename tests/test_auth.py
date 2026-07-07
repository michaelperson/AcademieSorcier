def test_login_succes(client, utilisateur_admin):
    reponse = client.post(
        "/login", json={"email": "admin@academie-sorcellerie.fr", "mot_de_passe": "admin123"}
    )

    assert reponse.status_code == 200
    corps = reponse.get_json()
    assert corps["role"] == "admin"
    assert corps["eleve_id"] is None
    assert corps["professeur_id"] is None


def test_login_email_inconnu(client):
    reponse = client.post(
        "/login", json={"email": "personne@academie-sorcellerie.fr", "mot_de_passe": "x"}
    )
    assert reponse.status_code == 401


def test_login_mauvais_mot_de_passe(client, utilisateur_admin):
    reponse = client.post(
        "/login", json={"email": "admin@academie-sorcellerie.fr", "mot_de_passe": "mauvais"}
    )
    assert reponse.status_code == 401


def test_login_champs_manquants(client):
    reponse = client.post("/login", json={"email": "admin@academie-sorcellerie.fr"})
    assert reponse.status_code == 400


def test_whoami_sans_header(client):
    reponse = client.get("/whoami")
    assert reponse.status_code == 401


def test_whoami_header_invalide(client):
    reponse = client.get("/whoami", headers={"X-User-Id": "pas-un-entier"})
    assert reponse.status_code == 401


def test_whoami_utilisateur_inexistant(client):
    reponse = client.get("/whoami", headers={"X-User-Id": "999999"})
    assert reponse.status_code == 401


def test_whoami_ok(client, utilisateur_admin):
    reponse = client.get("/whoami", headers={"X-User-Id": str(utilisateur_admin.id)})
    assert reponse.status_code == 200
    assert reponse.get_json()["role"] == "admin"

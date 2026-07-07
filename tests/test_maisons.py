def test_creer_maison(client):
    reponse = client.post(
        "/maisons",
        json={"nom": "Pyrraxis", "couleur": "Rouge et or", "fondateur": "Ignatius Brasier"},
    )
    assert reponse.status_code == 201
    corps = reponse.get_json()
    assert corps["nom"] == "Pyrraxis"
    assert corps["reputation"] == 0


def test_creer_maison_champ_manquant(client):
    reponse = client.post("/maisons", json={"nom": "Pyrraxis"})
    assert reponse.status_code == 400


def test_creer_maison_nom_deja_pris(client, maison):
    reponse = client.post(
        "/maisons",
        json={"nom": maison.nom, "couleur": "Autre", "fondateur": "Autre"},
    )
    assert reponse.status_code == 400


def test_lister_maisons(client, maison):
    reponse = client.get("/maisons")
    assert reponse.status_code == 200
    noms = [m["nom"] for m in reponse.get_json()]
    assert maison.nom in noms


def test_obtenir_maison(client, maison):
    reponse = client.get(f"/maisons/{maison.id}")
    assert reponse.status_code == 200
    assert reponse.get_json()["id"] == maison.id


def test_obtenir_maison_introuvable(client):
    reponse = client.get("/maisons/999999")
    assert reponse.status_code == 404


def test_modifier_maison(client, maison):
    reponse = client.put(f"/maisons/{maison.id}", json={"couleur": "Bleu nuit"})
    assert reponse.status_code == 200
    assert reponse.get_json()["couleur"] == "Bleu nuit"


def test_modifier_maison_introuvable(client):
    reponse = client.put("/maisons/999999", json={"couleur": "Bleu nuit"})
    assert reponse.status_code == 404


def test_supprimer_maison(client, maison):
    reponse = client.delete(f"/maisons/{maison.id}")
    assert reponse.status_code == 200

    reponse = client.get(f"/maisons/{maison.id}")
    assert reponse.status_code == 404

def test_creer_eleve(client, maison):
    reponse = client.post(
        "/eleves",
        json={"nom": "Alaric Corvenoire", "annee_etude": 3, "maison_id": maison.id},
    )
    assert reponse.status_code == 201
    corps = reponse.get_json()
    assert corps["statut"] == "actif"


def test_creer_eleve_annee_hors_bornes(client, maison):
    reponse = client.post(
        "/eleves",
        json={"nom": "Alaric Corvenoire", "annee_etude": 8, "maison_id": maison.id},
    )
    assert reponse.status_code == 400


def test_creer_eleve_maison_introuvable(client):
    reponse = client.post(
        "/eleves",
        json={"nom": "Alaric Corvenoire", "annee_etude": 3, "maison_id": 999999},
    )
    assert reponse.status_code == 400


def test_lister_eleves(client, eleve):
    reponse = client.get("/eleves")
    assert reponse.status_code == 200
    assert any(e["id"] == eleve.id for e in reponse.get_json())


def test_modifier_eleve_statut(client, eleve):
    reponse = client.put(f"/eleves/{eleve.id}", json={"statut": "diplome"})
    assert reponse.status_code == 200
    assert reponse.get_json()["statut"] == "diplome"


def test_modifier_eleve_statut_invalide(client, eleve):
    reponse = client.put(f"/eleves/{eleve.id}", json={"statut": "abandonne"})
    assert reponse.status_code == 400


def test_supprimer_eleve(client, eleve):
    reponse = client.delete(f"/eleves/{eleve.id}")
    assert reponse.status_code == 200
    assert client.get(f"/eleves/{eleve.id}").status_code == 404

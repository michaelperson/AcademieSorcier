def test_creer_professeur(client):
    reponse = client.post(
        "/professeurs",
        json={"nom": "Théodore Vance", "matiere_enseignee": "Potions", "anciennete": 15},
    )
    assert reponse.status_code == 201
    assert reponse.get_json()["nom"] == "Théodore Vance"


def test_creer_professeur_anciennete_invalide(client):
    reponse = client.post(
        "/professeurs",
        json={"nom": "Test", "matiere_enseignee": "Potions", "anciennete": "pas-un-nombre"},
    )
    assert reponse.status_code == 400


def test_lister_professeurs(client, professeur):
    reponse = client.get("/professeurs")
    assert reponse.status_code == 200
    assert any(p["id"] == professeur.id for p in reponse.get_json())


def test_obtenir_professeur_introuvable(client):
    reponse = client.get("/professeurs/999999")
    assert reponse.status_code == 404


def test_modifier_professeur(client, professeur):
    reponse = client.put(f"/professeurs/{professeur.id}", json={"anciennete": 16})
    assert reponse.status_code == 200
    assert reponse.get_json()["anciennete"] == 16


def test_supprimer_professeur(client, professeur):
    reponse = client.delete(f"/professeurs/{professeur.id}")
    assert reponse.status_code == 200
    assert client.get(f"/professeurs/{professeur.id}").status_code == 404

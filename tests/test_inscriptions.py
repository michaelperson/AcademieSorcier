from app.extensions import db


def test_inscrire_eleve(client, cours, eleve):
    reponse = client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    assert reponse.status_code == 201
    corps = reponse.get_json()
    assert corps["eleve_id"] == eleve.id
    assert corps["statut"] == "inscrit"


def test_inscrire_deux_fois_le_meme_eleve(client, cours, eleve):
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    reponse = client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    assert reponse.status_code == 400


def test_inscription_refusee_si_cours_complet(client, cours, eleve, eleve_2):
    """Test métier obligatoire du jour 2 : un élève ne peut pas s'inscrire
    à un cours complet.
    """
    cours.capacite_max = 1
    db.session.commit()

    premiere = client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    assert premiere.status_code == 201

    seconde = client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve_2.id})
    assert seconde.status_code == 400


def test_inscrire_eleve_introuvable(client, cours):
    reponse = client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": 999999})
    assert reponse.status_code == 400


def test_lister_eleves_du_cours(client, cours, eleve, eleve_2):
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve_2.id})

    reponse = client.get(f"/cours/{cours.id}/eleves")
    assert reponse.status_code == 200
    noms = {e["nom"] for e in reponse.get_json()}
    assert noms == {eleve.nom, eleve_2.nom}
    assert all(e["maison"] == eleve.maison.nom for e in reponse.get_json())


def test_lister_eleves_du_cours_eager(client, cours, eleve):
    """Le paramètre ?eager=true ne doit rien casser fonctionnellement,
    seulement changer la stratégie de chargement.
    """
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    reponse = client.get(f"/cours/{cours.id}/eleves?eager=true")
    assert reponse.status_code == 200
    assert reponse.get_json()[0]["nom"] == eleve.nom

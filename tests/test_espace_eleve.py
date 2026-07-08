def test_mes_cours(client, cours, eleve, utilisateur_eleve):
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})

    reponse = client.get("/moi/cours", headers={"X-User-Id": str(utilisateur_eleve.id)})
    assert reponse.status_code == 200
    assert reponse.get_json()[0]["cours_id"] == cours.id


def test_mes_cours_sans_header(client, eleve, utilisateur_eleve):
    reponse = client.get("/moi/cours")
    assert reponse.status_code == 401


def test_mes_cours_refuse_un_non_eleve(client, utilisateur_admin):
    """role_requis(ELEVE) doit refuser un rôle qui n'est pas élève."""
    reponse = client.get("/moi/cours", headers={"X-User-Id": str(utilisateur_admin.id)})
    assert reponse.status_code == 403


def test_mes_notes(client, cours, eleve, utilisateur_eleve):
    examen = client.post(
        f"/cours/{cours.id}/examens",
        json={"titre": "Interro 1", "date": "2026-03-01", "seuil_reussite": 10},
    ).get_json()
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(
        f"/examens/{examen['id']}/resultats",
        json={"resultats": [{"eleve_id": eleve.id, "note": 14}]},
    )

    reponse = client.get("/moi/notes", headers={"X-User-Id": str(utilisateur_eleve.id)})
    assert reponse.status_code == 200
    assert reponse.get_json()[0]["note"] == 14


def test_mon_dossier(client, eleve, utilisateur_eleve):
    reponse = client.get("/moi/dossier", headers={"X-User-Id": str(utilisateur_eleve.id)})
    assert reponse.status_code == 200
    corps = reponse.get_json()
    assert corps["nom"] == eleve.nom
    assert corps["maison"] == eleve.maison.nom

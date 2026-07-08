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


def test_mes_competences(client, cours, eleve, utilisateur_eleve, utilisateur_admin):
    entetes_admin = {"X-User-Id": str(utilisateur_admin.id)}
    examen = client.post(
        f"/cours/{cours.id}/examens",
        json={"titre": "Interro 1", "date": "2026-03-01", "seuil_reussite": 10},
    ).get_json()
    client.post(
        "/competences",
        json={
            "nom": "Sort de Stupéfixion",
            "categorie": "Sorts offensifs",
            "description": "Immobilise un adversaire à distance.",
            "condition_type": "examen",
            "examen_id": examen["id"],
            "note_min": 12,
        },
        headers=entetes_admin,
    )
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(
        f"/examens/{examen['id']}/resultats",
        json={"resultats": [{"eleve_id": eleve.id, "note": 15}]},
    )
    client.post(f"/examens/{examen['id']}/cloture")
    client.post(f"/examens/{examen['id']}/evaluer-competences")

    reponse = client.get("/moi/competences", headers={"X-User-Id": str(utilisateur_eleve.id)})
    assert reponse.status_code == 200
    corps = reponse.get_json()
    assert corps[0]["nom"] == "Sort de Stupéfixion"
    assert corps[0]["source"] == "examen"


def test_mes_tournois(client, eleve, eleve_2, utilisateur_eleve, utilisateur_admin):
    entetes_admin = {"X-User-Id": str(utilisateur_admin.id)}
    tournoi = client.post(
        "/tournois", json={"nom": "Tournoi de test", "annee": 2026}, headers=entetes_admin
    ).get_json()
    client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve_2.id, "vainqueur_id": eleve.id},
        headers=entetes_admin,
    )

    reponse = client.get("/moi/tournois", headers={"X-User-Id": str(utilisateur_eleve.id)})
    assert reponse.status_code == 200
    corps = reponse.get_json()
    assert corps[0]["issue"] == "gagne"
    assert corps[0]["adversaire"]["nom"] == eleve_2.nom

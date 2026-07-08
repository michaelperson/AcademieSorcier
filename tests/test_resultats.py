def _creer_examen_et_notes(client, cours, eleve, eleve_2):
    examen = client.post(
        f"/cours/{cours.id}/examens",
        json={"titre": "Interro 1", "date": "2026-03-01", "seuil_reussite": 10},
    ).get_json()
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve_2.id})
    client.post(
        f"/examens/{examen['id']}/resultats",
        json={
            "resultats": [
                {"eleve_id": eleve.id, "note": 16},
                {"eleve_id": eleve_2.id, "note": 8},
            ]
        },
    )
    return examen


def test_lister_resultats_par_examen(client, cours, eleve, eleve_2):
    examen = _creer_examen_et_notes(client, cours, eleve, eleve_2)

    reponse = client.get(f"/resultats?examen_id={examen['id']}")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 2


def test_lister_resultats_par_cours(client, cours, eleve, eleve_2):
    _creer_examen_et_notes(client, cours, eleve, eleve_2)

    reponse = client.get(f"/resultats?cours_id={cours.id}")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 2


def test_moyenne_du_cours(client, cours, eleve, eleve_2):
    _creer_examen_et_notes(client, cours, eleve, eleve_2)

    reponse = client.get(f"/cours/{cours.id}/moyenne")
    assert reponse.status_code == 200
    corps = reponse.get_json()
    assert corps["moyenne"] == 12.0
    assert corps["nombre_resultats"] == 2


def test_moyenne_du_cours_sans_resultat(client, cours):
    reponse = client.get(f"/cours/{cours.id}/moyenne")
    assert reponse.status_code == 200
    assert reponse.get_json()["moyenne"] is None

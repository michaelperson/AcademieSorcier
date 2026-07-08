import pytest


@pytest.fixture
def examen(client, cours):
    reponse = client.post(
        f"/cours/{cours.id}/examens",
        json={"titre": "Interrogation 1", "date": "2026-03-01", "seuil_reussite": 10},
    )
    assert reponse.status_code == 201
    return reponse.get_json()


def test_creer_examen(client, cours):
    reponse = client.post(
        f"/cours/{cours.id}/examens",
        json={"titre": "Interrogation 1", "date": "2026-03-01", "seuil_reussite": 10},
    )
    assert reponse.status_code == 201
    assert reponse.get_json()["titre"] == "Interrogation 1"


def test_creer_examen_date_invalide(client, cours):
    reponse = client.post(
        f"/cours/{cours.id}/examens",
        json={"titre": "Interrogation 1", "date": "01/03/2026", "seuil_reussite": 10},
    )
    assert reponse.status_code == 400


def test_saisir_resultats_en_masse(client, cours, eleve, eleve_2, examen):
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve_2.id})

    payload = {
        "resultats": [
            {"eleve_id": eleve.id, "note": 15},
            {"eleve_id": eleve_2.id, "note": 8},
        ]
    }
    reponse = client.post(f"/examens/{examen['id']}/resultats", json=payload)
    assert reponse.status_code == 201
    notes = {r["eleve_id"]: r["note"] for r in reponse.get_json()}
    assert notes[eleve.id] == 15
    assert notes[eleve_2.id] == 8
    # Tant que l'examen n'est pas clôturé, aucun résultat n'a de statut.
    assert all(r["statut"] is None for r in reponse.get_json())


def test_saisir_resultats_note_hors_bornes_annule_tout(client, cours, eleve, eleve_2, examen):
    """Validation atomique : une seule note invalide dans le lot doit
    rejeter tout le payload, pas seulement l'entrée fautive.
    """
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve_2.id})

    payload = {
        "resultats": [
            {"eleve_id": eleve.id, "note": 15},
            {"eleve_id": eleve_2.id, "note": 25},
        ]
    }
    reponse = client.post(f"/examens/{examen['id']}/resultats", json=payload)
    assert reponse.status_code == 400

    verif = client.get(f"/examens/{examen['id']}/resultats")
    assert verif.get_json() == []


def test_saisir_resultats_eleve_non_inscrit(client, eleve, examen):
    payload = {"resultats": [{"eleve_id": eleve.id, "note": 15}]}
    reponse = client.post(f"/examens/{examen['id']}/resultats", json=payload)
    assert reponse.status_code == 400


def test_reecrire_une_note_efface_son_statut(client, cours, eleve, examen):
    """Modifier la note d'un élève après clôture invalide la décision
    précédente : le statut repasse à None tant que l'examen n'est pas
    reclôturé sur la nouvelle note.
    """
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(
        f"/examens/{examen['id']}/resultats",
        json={"resultats": [{"eleve_id": eleve.id, "note": 15}]},
    )
    client.post(f"/examens/{examen['id']}/cloture")

    client.post(
        f"/examens/{examen['id']}/resultats",
        json={"resultats": [{"eleve_id": eleve.id, "note": 4}]},
    )
    resultats = client.get(f"/examens/{examen['id']}/resultats").get_json()
    assert resultats[0]["note"] == 4
    assert resultats[0]["statut"] is None


def test_cloture_examen_decide_reussi_echec_par_examen(client, cours, eleve, eleve_2, examen):
    """Test métier obligatoire du jour 2 (version révisée) : la clôture
    d'un examen fixe le statut réussi/échec sur le RÉSULTAT de chaque
    élève pour cet examen — pas sur son inscription au cours, qui est une
    décision séparée (voir test_cloture_cours*).
    """
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve_2.id})

    client.post(
        f"/examens/{examen['id']}/resultats",
        json={
            "resultats": [
                {"eleve_id": eleve.id, "note": 15},  # au-dessus du seuil (10)
                {"eleve_id": eleve_2.id, "note": 4},  # en dessous
            ]
        },
    )

    reponse = client.post(f"/examens/{examen['id']}/cloture")
    assert reponse.status_code == 200
    corps = reponse.get_json()

    statuts = {r["eleve_id"]: r["statut"] for r in corps["resultats"]}
    assert statuts[eleve.id] == "reussi"
    assert statuts[eleve_2.id] == "echec"

    # L'inscription, elle, n'a pas bougé : ce n'est pas le rôle de cet endpoint.
    mes_cours = client.get(f"/cours/{cours.id}/eleves").get_json()
    inscription_eleve = next(e for e in mes_cours if e["eleve_id"] == eleve.id)
    assert inscription_eleve["statut_inscription"] == "inscrit"


def test_cloture_examen_refusee_si_resultat_manquant(client, cours, eleve, eleve_2, examen):
    """Un élève inscrit et sans résultat bloque la clôture : on ne décide
    pas à sa place.
    """
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve_2.id})
    client.post(
        f"/examens/{examen['id']}/resultats",
        json={"resultats": [{"eleve_id": eleve.id, "note": 15}]},
    )

    reponse = client.post(f"/examens/{examen['id']}/cloture")
    assert reponse.status_code == 400
    assert eleve_2.id in reponse.get_json()["eleves_sans_resultat"]


def test_cloture_examen_sans_resultats(client, examen):
    reponse = client.post(f"/examens/{examen['id']}/cloture")
    assert reponse.status_code == 400


def test_cloture_examen_est_idempotente(client, cours, eleve, examen):
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(
        f"/examens/{examen['id']}/resultats",
        json={"resultats": [{"eleve_id": eleve.id, "note": 15}]},
    )

    premiere = client.post(f"/examens/{examen['id']}/cloture").get_json()
    seconde = client.post(f"/examens/{examen['id']}/cloture").get_json()
    assert premiere == seconde


def test_cloture_cours_sans_eleve_id_est_un_rapport_en_lecture_seule(
    client, cours, eleve, eleve_2, examen
):
    """Sans ?eleve_id=, l'endpoint renvoie la situation de toute la classe
    sans rien écrire en base — aucune inscription ne doit changer.
    """
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve_2.id})
    client.post(
        f"/examens/{examen['id']}/resultats",
        json={
            "resultats": [
                {"eleve_id": eleve.id, "note": 15},
                {"eleve_id": eleve_2.id, "note": 4},
            ]
        },
    )

    reponse = client.post(f"/cours/{cours.id}/cloture")
    assert reponse.status_code == 200
    corps = reponse.get_json()
    assert corps["intitule"] == cours.intitule
    statuts = {e["eleve_id"]: e["statut"] for e in corps["eleves"]}
    assert statuts[eleve.id] == "reussi"
    assert statuts[eleve_2.id] == "echec"

    # Toujours "inscrit" : le mode rapport ne mute rien.
    mes_cours = client.get(f"/cours/{cours.id}/eleves").get_json()
    assert all(e["statut_inscription"] == "inscrit" for e in mes_cours)


def test_cloture_cours_avec_eleve_id_met_a_jour_l_inscription(client, cours, eleve, examen):
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(
        f"/examens/{examen['id']}/resultats",
        json={"resultats": [{"eleve_id": eleve.id, "note": 15}]},
    )

    reponse = client.post(f"/cours/{cours.id}/cloture?eleve_id={eleve.id}")
    assert reponse.status_code == 200
    corps = reponse.get_json()
    assert corps["decision_finale"] == "reussi"
    assert corps["nouveau_statut_inscription"] == "valide"
    assert corps["cours"]["intitule"] == cours.intitule
    assert corps["eleve"]["nom"] == eleve.nom
    assert corps["resultats"][0]["note"] == 15

    mes_cours = client.get(f"/cours/{cours.id}/eleves").get_json()
    inscription_eleve = next(e for e in mes_cours if e["eleve_id"] == eleve.id)
    assert inscription_eleve["statut_inscription"] == "valide"


def test_cloture_cours_avec_eleve_id_ne_touche_pas_les_autres(
    client, cours, eleve, eleve_2, examen
):
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve_2.id})
    client.post(
        f"/examens/{examen['id']}/resultats",
        json={
            "resultats": [
                {"eleve_id": eleve.id, "note": 15},
                {"eleve_id": eleve_2.id, "note": 4},
            ]
        },
    )

    client.post(f"/cours/{cours.id}/cloture?eleve_id={eleve.id}")

    mes_cours = client.get(f"/cours/{cours.id}/eleves").get_json()
    statuts = {e["eleve_id"]: e["statut_inscription"] for e in mes_cours}
    assert statuts[eleve.id] == "valide"
    assert statuts[eleve_2.id] == "inscrit"  # non ciblé, non touché


def test_cloture_cours_sans_resultat_refuse(client, cours, eleve):
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    reponse = client.post(f"/cours/{cours.id}/cloture?eleve_id={eleve.id}")
    assert reponse.status_code == 400


def test_cloture_cours_eleve_non_inscrit(client, cours, eleve):
    reponse = client.post(f"/cours/{cours.id}/cloture?eleve_id={eleve.id}")
    assert reponse.status_code == 404


def _entetes_admin(utilisateur_admin):
    return {"X-User-Id": str(utilisateur_admin.id)}


def _creer_competence_examen(client, examen, note_min, utilisateur_admin, nom="Sort de Stupéfixion"):
    return client.post(
        "/competences",
        json={
            "nom": nom,
            "categorie": "Sorts offensifs",
            "description": "Immobilise un adversaire à distance.",
            "condition_type": "examen",
            "examen_id": examen["id"],
            "note_min": note_min,
        },
        headers=_entetes_admin(utilisateur_admin),
    ).get_json()


def test_evaluer_competences_debloque_maitrise_si_seuil_atteint(
    client, cours, eleve, eleve_2, examen, utilisateur_admin
):
    """Test métier du jour 3 : évaluer les compétences après une clôture
    d'examen débloque une Maitrise seulement pour les élèves dont la note
    atteint le seuil PROPRE à la compétence (pas forcément celui de
    l'examen).
    """
    _creer_competence_examen(client, examen, note_min=12, utilisateur_admin=utilisateur_admin)

    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve_2.id})
    client.post(
        f"/examens/{examen['id']}/resultats",
        json={
            "resultats": [
                {"eleve_id": eleve.id, "note": 15},  # au-dessus du seuil de la compétence (12)
                {"eleve_id": eleve_2.id, "note": 11},  # en dessous
            ]
        },
    )
    client.post(f"/examens/{examen['id']}/cloture")

    reponse = client.post(f"/examens/{examen['id']}/evaluer-competences")
    assert reponse.status_code == 200
    corps = reponse.get_json()
    eleves_debloques = {m["eleve_id"] for m in corps["maitrises_creees"]}
    assert eleves_debloques == {eleve.id}


def test_evaluer_competences_refuse_si_examen_pas_cloture(
    client, cours, eleve, examen, utilisateur_admin
):
    _creer_competence_examen(client, examen, note_min=12, utilisateur_admin=utilisateur_admin)
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(
        f"/examens/{examen['id']}/resultats",
        json={"resultats": [{"eleve_id": eleve.id, "note": 15}]},
    )

    reponse = client.post(f"/examens/{examen['id']}/evaluer-competences")
    assert reponse.status_code == 400


def test_evaluer_competences_est_idempotent(client, cours, eleve, examen, utilisateur_admin):
    """Idempotence obligatoire du jour 3 : un élève qui repasse au-dessus
    du même seuil ne débloque jamais deux fois la même compétence.
    """
    _creer_competence_examen(client, examen, note_min=12, utilisateur_admin=utilisateur_admin)
    client.post(f"/cours/{cours.id}/inscriptions", json={"eleve_id": eleve.id})
    client.post(
        f"/examens/{examen['id']}/resultats",
        json={"resultats": [{"eleve_id": eleve.id, "note": 15}]},
    )
    client.post(f"/examens/{examen['id']}/cloture")

    premiere = client.post(f"/examens/{examen['id']}/evaluer-competences").get_json()
    assert len(premiere["maitrises_creees"]) == 1
    assert len(premiere["deja_debloquees"]) == 0

    seconde = client.post(f"/examens/{examen['id']}/evaluer-competences").get_json()
    assert len(seconde["maitrises_creees"]) == 0
    assert len(seconde["deja_debloquees"]) == 1

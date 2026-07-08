import pytest


@pytest.fixture
def examen(client, cours):
    reponse = client.post(
        f"/cours/{cours.id}/examens",
        json={"titre": "Interrogation 1", "date": "2026-03-01", "seuil_reussite": 10},
    )
    assert reponse.status_code == 201
    return reponse.get_json()


def _entetes_admin(utilisateur_admin):
    return {"X-User-Id": str(utilisateur_admin.id)}


def test_creer_competence_condition_examen(client, examen, utilisateur_admin):
    reponse = client.post(
        "/competences",
        json={
            "nom": "Sort de Stupéfixion",
            "categorie": "Sorts offensifs",
            "description": "Immobilise un adversaire à distance.",
            "condition_type": "examen",
            "examen_id": examen["id"],
            "note_min": 12,
        },
        headers=_entetes_admin(utilisateur_admin),
    )
    assert reponse.status_code == 201
    corps = reponse.get_json()
    assert corps["condition_type"] == "examen"
    assert corps["examen_id"] == examen["id"]
    assert corps["note_min"] == 12


def test_creer_competence_condition_tournoi_sans_examen(client, utilisateur_admin):
    reponse = client.post(
        "/competences",
        json={
            "nom": "Titre de Champion du Tournoi",
            "categorie": "Tournoi",
            "description": "Accordée au vainqueur d'un tournoi.",
            "condition_type": "tournoi",
        },
        headers=_entetes_admin(utilisateur_admin),
    )
    assert reponse.status_code == 201
    corps = reponse.get_json()
    assert corps["examen_id"] is None
    assert corps["note_min"] is None


def test_creer_competence_examen_sans_note_min_refusee(client, examen, utilisateur_admin):
    reponse = client.post(
        "/competences",
        json={
            "nom": "Compétence incomplète",
            "categorie": "Potions",
            "description": "...",
            "condition_type": "examen",
            "examen_id": examen["id"],
        },
        headers=_entetes_admin(utilisateur_admin),
    )
    assert reponse.status_code == 400


def test_creer_competence_refusee_sans_header(client):
    reponse = client.post(
        "/competences",
        json={
            "nom": "X",
            "categorie": "Y",
            "description": "Z",
            "condition_type": "tournoi",
        },
    )
    assert reponse.status_code == 401


def test_creer_competence_refusee_pour_un_eleve(client, eleve, utilisateur_eleve):
    reponse = client.post(
        "/competences",
        json={
            "nom": "X",
            "categorie": "Y",
            "description": "Z",
            "condition_type": "tournoi",
        },
        headers={"X-User-Id": str(utilisateur_eleve.id)},
    )
    assert reponse.status_code == 403


def test_lister_competences_filtrable_par_categorie(client, examen, utilisateur_admin):
    entetes = _entetes_admin(utilisateur_admin)
    client.post(
        "/competences",
        json={
            "nom": "Compétence Potions",
            "categorie": "Potions",
            "description": "...",
            "condition_type": "examen",
            "examen_id": examen["id"],
            "note_min": 10,
        },
        headers=entetes,
    )
    client.post(
        "/competences",
        json={
            "nom": "Compétence Tournoi",
            "categorie": "Tournoi",
            "description": "...",
            "condition_type": "tournoi",
        },
        headers=entetes,
    )

    reponse = client.get("/competences?categorie=Potions")
    assert reponse.status_code == 200
    corps = reponse.get_json()
    assert corps["total"] == 1
    assert corps["elements"][0]["categorie"] == "Potions"


def test_lister_competences_paginee(client, examen, utilisateur_admin):
    entetes = _entetes_admin(utilisateur_admin)
    for i in range(5):
        client.post(
            "/competences",
            json={
                "nom": f"Compétence {i}",
                "categorie": "Potions",
                "description": "...",
                "condition_type": "examen",
                "examen_id": examen["id"],
                "note_min": 10,
            },
            headers=entetes,
        )

    reponse = client.get("/competences?par_page=2&page=1")
    corps = reponse.get_json()
    assert corps["total"] == 5
    assert corps["par_page"] == 2
    assert len(corps["elements"]) == 2
    assert corps["pages"] == 3


def test_modifier_competence(client, examen, utilisateur_admin):
    entetes = _entetes_admin(utilisateur_admin)
    creation = client.post(
        "/competences",
        json={
            "nom": "Compétence à modifier",
            "categorie": "Potions",
            "description": "Ancienne description.",
            "condition_type": "examen",
            "examen_id": examen["id"],
            "note_min": 10,
        },
        headers=entetes,
    ).get_json()

    reponse = client.put(
        f"/competences/{creation['id']}",
        json={"description": "Nouvelle description."},
        headers=entetes,
    )
    assert reponse.status_code == 200
    assert reponse.get_json()["description"] == "Nouvelle description."


def test_supprimer_competence(client, examen, utilisateur_admin):
    entetes = _entetes_admin(utilisateur_admin)
    creation = client.post(
        "/competences",
        json={
            "nom": "Compétence à supprimer",
            "categorie": "Potions",
            "description": "...",
            "condition_type": "examen",
            "examen_id": examen["id"],
            "note_min": 10,
        },
        headers=entetes,
    ).get_json()

    reponse = client.delete(f"/competences/{creation['id']}", headers=entetes)
    assert reponse.status_code == 200
    assert client.get(f"/competences/{creation['id']}").status_code == 404

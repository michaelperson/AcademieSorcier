"""
Validation stricte des payloads (jour 4) : un échantillon représentatif
plutôt qu'un test par champ de chaque ressource (déjà couvert
indirectement par les fichiers de tests de chaque jour). Ce qu'on vérifie
ici spécifiquement : le format de réponse (`erreur` + `champs`) et que le
champ fautif est bien celui qu'on attend, pas juste un 400 générique.
"""

from app.extensions import db
from app.dal.models import Examen


def _entetes_admin(utilisateur_admin):
    return {"X-User-Id": str(utilisateur_admin.id)}


def test_creer_maison_champs_manquants(client):
    reponse = client.post("/maisons", json={"nom": "Sans le reste"})
    assert reponse.status_code == 400
    corps = reponse.get_json()
    assert corps["erreur"] == "Payload invalide."
    assert "couleur" in corps["champs"]
    assert "fondateur" in corps["champs"]
    assert "nom" not in corps["champs"]


def test_creer_eleve_annee_etude_hors_bornes(client, maison):
    reponse = client.post("/eleves", json={"nom": "Test", "annee_etude": 12, "maison_id": maison.id})
    assert reponse.status_code == 400
    corps = reponse.get_json()
    assert "annee_etude" in corps["champs"]


def test_creer_eleve_maison_id_type_invalide(client):
    reponse = client.post("/eleves", json={"nom": "Test", "annee_etude": 3, "maison_id": "pas-un-entier"})
    assert reponse.status_code == 400
    assert "maison_id" in reponse.get_json()["champs"]


def test_saisir_resultat_note_negative(client, cours):
    reponse_examen = client.post(
        f"/cours/{cours.id}/examens",
        json={"titre": "Examen", "date": "2026-05-01", "seuil_reussite": 10},
    )
    examen_id = reponse_examen.get_json()["id"]

    reponse = client.post(
        f"/examens/{examen_id}/resultats",
        json={"resultats": [{"eleve_id": 1, "note": -5}]},
    )
    assert reponse.status_code == 400
    corps = reponse.get_json()
    assert corps["champs"]["resultats"]["0"]["note"]


def test_saisir_resultat_note_superieure_au_maximum(client, cours):
    reponse_examen = client.post(
        f"/cours/{cours.id}/examens",
        json={"titre": "Examen", "date": "2026-05-01", "seuil_reussite": 10},
    )
    examen_id = reponse_examen.get_json()["id"]

    reponse = client.post(
        f"/examens/{examen_id}/resultats",
        json={"resultats": [{"eleve_id": 1, "note": 25}]},
    )
    assert reponse.status_code == 400
    corps = reponse.get_json()
    assert "20" in corps["champs"]["resultats"]["0"]["note"][0]


def test_creer_examen_date_invalide(client, cours):
    reponse = client.post(
        f"/cours/{cours.id}/examens",
        json={"titre": "Examen", "date": "01-05-2026", "seuil_reussite": 10},
    )
    assert reponse.status_code == 400
    assert "date" in reponse.get_json()["champs"]


def test_enregistrer_duel_vainqueur_hors_participants(client, eleve, eleve_2, utilisateur_admin):
    entetes = _entetes_admin(utilisateur_admin)
    tournoi = client.post("/tournois", json={"nom": "T", "annee": 2026}, headers=entetes).get_json()

    reponse = client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve_2.id, "vainqueur_id": 9999},
        headers=entetes,
    )
    assert reponse.status_code == 400
    assert "vainqueur_id" in reponse.get_json()["champs"]


def test_creer_competence_categorie_manquante(client, utilisateur_admin):
    reponse = client.post(
        "/competences",
        json={"nom": "X", "description": "Y", "condition_type": "tournoi"},
        headers=_entetes_admin(utilisateur_admin),
    )
    assert reponse.status_code == 400
    assert "categorie" in reponse.get_json()["champs"]

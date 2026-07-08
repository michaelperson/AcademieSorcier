import pytest


def _entetes_admin(utilisateur_admin):
    return {"X-User-Id": str(utilisateur_admin.id)}


@pytest.fixture
def tournoi(client, utilisateur_admin):
    reponse = client.post(
        "/tournois",
        json={"nom": "Tournoi de printemps", "annee": 2026},
        headers=_entetes_admin(utilisateur_admin),
    )
    assert reponse.status_code == 201
    return reponse.get_json()


def test_creer_tournoi(client, utilisateur_admin):
    reponse = client.post(
        "/tournois",
        json={"nom": "Tournoi d'automne", "annee": 2026},
        headers=_entetes_admin(utilisateur_admin),
    )
    assert reponse.status_code == 201
    assert reponse.get_json()["cloture_le"] is None


def test_creer_tournoi_refuse_sans_admin(client, eleve, utilisateur_eleve):
    reponse = client.post(
        "/tournois",
        json={"nom": "Tournoi interdit", "annee": 2026},
        headers={"X-User-Id": str(utilisateur_eleve.id)},
    )
    assert reponse.status_code == 403


def test_lister_tournois_filtrable_par_annee(client, tournoi, utilisateur_admin):
    client.post(
        "/tournois",
        json={"nom": "Tournoi ancien", "annee": 2020},
        headers=_entetes_admin(utilisateur_admin),
    )

    reponse = client.get("/tournois?annee=2026")
    corps = reponse.get_json()
    assert corps["total"] == 1
    assert corps["elements"][0]["nom"] == "Tournoi de printemps"


def test_enregistrer_duel(client, tournoi, eleve, eleve_2, utilisateur_admin):
    reponse = client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve_2.id, "vainqueur_id": eleve.id},
        headers=_entetes_admin(utilisateur_admin),
    )
    assert reponse.status_code == 201
    assert reponse.get_json()["vainqueur_id"] == eleve.id


def test_enregistrer_duel_refuse_meme_eleve(client, tournoi, eleve, utilisateur_admin):
    reponse = client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve.id, "vainqueur_id": eleve.id},
        headers=_entetes_admin(utilisateur_admin),
    )
    assert reponse.status_code == 400


def test_enregistrer_duel_refuse_vainqueur_hors_duel(client, tournoi, eleve, eleve_2, utilisateur_admin):
    reponse = client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve_2.id, "vainqueur_id": 9999},
        headers=_entetes_admin(utilisateur_admin),
    )
    assert reponse.status_code == 400


def test_lister_duels(client, tournoi, eleve, eleve_2, utilisateur_admin):
    entetes = _entetes_admin(utilisateur_admin)
    client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve_2.id, "vainqueur_id": eleve.id},
        headers=entetes,
    )

    reponse = client.get(f"/tournois/{tournoi['id']}/duels")
    assert reponse.status_code == 200
    duels = reponse.get_json()
    assert len(duels) == 1
    assert duels[0]["vainqueur"]["nom"] == eleve.nom


def test_cloturer_tournoi_designe_vainqueur_et_ajoute_reputation(
    client, tournoi, eleve, eleve_2, utilisateur_admin
):
    entetes = _entetes_admin(utilisateur_admin)
    client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve_2.id, "vainqueur_id": eleve.id},
        headers=entetes,
    )

    reputation_avant = eleve.maison.reputation

    reponse = client.post(f"/tournois/{tournoi['id']}/cloture", headers=entetes)
    assert reponse.status_code == 200
    corps = reponse.get_json()
    assert corps["vainqueur_eleve_id"] == eleve.id
    assert corps["nouvelle_reputation"] == reputation_avant + corps["reputation_ajoutee"]

    fiche_tournoi = client.get(f"/tournois/{tournoi['id']}").get_json()
    assert fiche_tournoi["vainqueur_eleve_id"] == eleve.id
    assert fiche_tournoi["cloture_le"] is not None


def test_cloturer_tournoi_debloque_competence_tournoi(
    client, tournoi, eleve, eleve_2, utilisateur_admin
):
    entetes = _entetes_admin(utilisateur_admin)
    client.post(
        "/competences",
        json={
            "nom": "Titre de Champion du Tournoi",
            "categorie": "Tournoi",
            "description": "...",
            "condition_type": "tournoi",
        },
        headers=entetes,
    )
    client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve_2.id, "vainqueur_id": eleve.id},
        headers=entetes,
    )

    reponse = client.post(f"/tournois/{tournoi['id']}/cloture", headers=entetes)
    assert reponse.get_json()["competences_debloquees"] == ["Titre de Champion du Tournoi"]


def test_cloturer_tournoi_refuse_un_second_rejeu(client, tournoi, eleve, eleve_2, utilisateur_admin):
    entetes = _entetes_admin(utilisateur_admin)
    client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve_2.id, "vainqueur_id": eleve.id},
        headers=entetes,
    )
    client.post(f"/tournois/{tournoi['id']}/cloture", headers=entetes)

    reponse = client.post(f"/tournois/{tournoi['id']}/cloture", headers=entetes)
    assert reponse.status_code == 400


def test_enregistrer_duel_refuse_si_tournoi_deja_cloture(
    client, tournoi, eleve, eleve_2, utilisateur_admin
):
    entetes = _entetes_admin(utilisateur_admin)
    client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve_2.id, "vainqueur_id": eleve.id},
        headers=entetes,
    )
    client.post(f"/tournois/{tournoi['id']}/cloture", headers=entetes)

    reponse = client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve_2.id, "vainqueur_id": eleve.id},
        headers=entetes,
    )
    assert reponse.status_code == 400


def test_cloturer_tournoi_sans_duel_refuse(client, tournoi, utilisateur_admin):
    reponse = client.post(f"/tournois/{tournoi['id']}/cloture", headers=_entetes_admin(utilisateur_admin))
    assert reponse.status_code == 400


def test_cloturer_tournoi_egalite_ne_designe_aucun_vainqueur(
    client, tournoi, eleve, eleve_2, utilisateur_admin
):
    """Deux duels entre les deux mêmes élèves, un gagné chacun : égalité
    stricte, la clôture doit être refusée plutôt que de trancher au hasard.
    """
    entetes = _entetes_admin(utilisateur_admin)
    client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve_2.id, "vainqueur_id": eleve.id},
        headers=entetes,
    )
    client.post(
        f"/tournois/{tournoi['id']}/duels",
        json={"eleve_1_id": eleve.id, "eleve_2_id": eleve_2.id, "vainqueur_id": eleve_2.id},
        headers=entetes,
    )

    reponse = client.post(f"/tournois/{tournoi['id']}/cloture", headers=entetes)
    assert reponse.status_code == 400
    corps = reponse.get_json()
    assert sorted(corps["eleves_ex_aequo"]) == sorted([eleve.id, eleve_2.id])

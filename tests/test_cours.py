def test_creer_cours(client, professeur, annee_academique):
    reponse = client.post(
        "/cours",
        json={
            "intitule": "Potions avancées",
            "niveau_requis": 4,
            "capacite_max": 25,
            "professeur_id": professeur.id,
        },
    )
    assert reponse.status_code == 201
    corps = reponse.get_json()
    assert corps["intitule"] == "Potions avancées"
    assert corps["annee_academique_id"] == annee_academique.id


def test_creer_cours_sans_annee_academique(client, professeur):
    # Aucune AnneeAcademique en base : la création doit être refusée
    # proprement plutôt que planter sur une contrainte de clé étrangère.
    reponse = client.post(
        "/cours",
        json={
            "intitule": "Potions avancées",
            "niveau_requis": 4,
            "capacite_max": 25,
            "professeur_id": professeur.id,
        },
    )
    assert reponse.status_code == 400


def test_creer_cours_professeur_introuvable(client, annee_academique):
    reponse = client.post(
        "/cours",
        json={
            "intitule": "Potions avancées",
            "niveau_requis": 4,
            "capacite_max": 25,
            "professeur_id": 999999,
        },
    )
    assert reponse.status_code == 400


def test_lister_cours(client, professeur, annee_academique):
    client.post(
        "/cours",
        json={
            "intitule": "Potions avancées",
            "niveau_requis": 4,
            "capacite_max": 25,
            "professeur_id": professeur.id,
        },
    )
    reponse = client.get("/cours")
    assert reponse.status_code == 200
    assert len(reponse.get_json()) == 1


def test_modifier_cours(client, professeur, annee_academique):
    creation = client.post(
        "/cours",
        json={
            "intitule": "Potions avancées",
            "niveau_requis": 4,
            "capacite_max": 25,
            "professeur_id": professeur.id,
        },
    )
    cours_id = creation.get_json()["id"]

    reponse = client.put(f"/cours/{cours_id}", json={"capacite_max": 30})
    assert reponse.status_code == 200
    assert reponse.get_json()["capacite_max"] == 30


def test_supprimer_cours(client, professeur, annee_academique):
    creation = client.post(
        "/cours",
        json={
            "intitule": "Potions avancées",
            "niveau_requis": 4,
            "capacite_max": 25,
            "professeur_id": professeur.id,
        },
    )
    cours_id = creation.get_json()["id"]

    reponse = client.delete(f"/cours/{cours_id}")
    assert reponse.status_code == 200
    assert client.get(f"/cours/{cours_id}").status_code == 404

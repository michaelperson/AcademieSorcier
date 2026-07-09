"""
Couche d'accès aux données (DAL) : tout ce qui décrit une forme de
donnée vit ici, dans deux sous-dossiers distincts.

- app/dal/models/ : les entités SQLAlchemy, mappées sur les tables de la
  base (ce qu'on lit et écrit en persistance).
- app/dal/dto/ : les DTOs de sortie, des dataclasses qui décrivent la
  forme des réponses JSON (ce qu'on renvoie au client).

Les deux ne doivent pas se confondre : un modèle porte des relations
SQLAlchemy et de la logique de persistance, un DTO ne porte que des
champs simples prêts à sérialiser. Regrouper les deux sous "dal" reflète
que ce sont, l'un comme l'autre, des définitions de structure de données
plutôt que de la logique de route ou de validation (qui restent dans
app/routes/ et app/schemas.py).
"""

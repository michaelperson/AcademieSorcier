"""
Point de passage unique entre un schéma marshmallow (app/schemas.py) et une
route Flask : charge le JSON de la requête à travers le schéma, et
transforme un échec de validation en la même forme de réponse partout
dans l'API.

Format d'erreur (400) :

    {
        "erreur": "Payload invalide.",
        "champs": {
            "note": ["Doit être compris entre 0 et 20."],
            "eleve_id": ["Ce champ est requis."]
        }
    }

`champs` reprend directement `ValidationError.messages` de marshmallow :
une clé par champ fautif, une liste de messages (généralement un seul)
par clé. C'est ce format que le cahier des charges du jour 4 demande
("un message qui indique précisément quel champ pose problème").
"""

from flask import jsonify
from marshmallow import ValidationError


def valider(schema, payload, partial=False):
    """Valide `payload` (dict déjà désérialisé, ou None) avec `schema`.

    Retourne (donnees, erreur_reponse) :
    - en cas de succès, `donnees` est le dict validé/nettoyé par
      marshmallow et `erreur_reponse` vaut None.
    - en cas d'échec, `donnees` vaut None et `erreur_reponse` est un tuple
      (reponse_flask, 400) prêt à être renvoyé tel quel par la vue :

          donnees, erreur = valider(MaisonSchema(), request.get_json(silent=True))
          if erreur:
              return erreur
    """
    try:
        return schema.load(payload or {}, partial=partial), None
    except ValidationError as exc:
        return None, (jsonify({"erreur": "Payload invalide.", "champs": exc.messages}), 400)

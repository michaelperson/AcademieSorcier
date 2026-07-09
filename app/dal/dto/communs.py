"""
Le point de passage commun à tous les DTOs (`vers_dict`) et les fragments
réutilisés par plusieurs d'entre eux — pour l'instant, `EleveMinimalDTO`
seul (un élève réduit à id/nom, utilisé partout où une réponse a besoin
de nommer un élève sans reprendre toute sa fiche).
"""

from dataclasses import asdict, dataclass


def vers_dict(dto) -> dict:
    """Convertit un DTO (n'importe laquelle des dataclasses de ce paquet)
    en dict prêt pour jsonify(). Un seul point de passage plutôt qu'un
    dataclasses.asdict() répété dans chaque route. Fonctionne aussi pour
    les DTOs imbriqués : asdict() est récursif.
    """
    return asdict(dto)


@dataclass
class EleveMinimalDTO:
    id: int
    nom: str

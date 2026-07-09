from dataclasses import dataclass
from typing import List, Optional

from app.dal.dto.communs import EleveMinimalDTO


@dataclass
class TournoiDTO:
    id: int
    nom: str
    annee: int
    maison_organisatrice_id: Optional[int]
    vainqueur_eleve_id: Optional[int]
    cloture_le: Optional[str]


@dataclass
class DuelDTO:
    id: int
    tournoi_id: int
    eleve_1_id: int
    eleve_2_id: int
    vainqueur_id: Optional[int]


@dataclass
class DuelDetailleDTO:
    """Utilisée par GET /tournois/<id>/duels : les participants sont
    donnés par nom (EleveMinimalDTO), pas juste par id, contrairement à
    DuelDTO ci-dessus.
    """

    id: int
    eleve_1: EleveMinimalDTO
    eleve_2: EleveMinimalDTO
    vainqueur: Optional[EleveMinimalDTO]


@dataclass
class ClotureTournoiDTO:
    tournoi_id: int
    vainqueur_eleve_id: int
    victoires: int
    competences_debloquees: List[str]
    maison_id: int
    reputation_ajoutee: int
    nouvelle_reputation: int

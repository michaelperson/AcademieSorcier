from dataclasses import dataclass
from typing import Optional


@dataclass
class ResultatDetailleDTO:
    """Forme utilisée par app/routes/resultats.py : le listing global des
    résultats (filtrable par cours ou examen) a besoin de préciser à quel
    cours chaque résultat appartient, contrairement à ResultatDTO
    (app/dal/dto/examens.py) où cette information est déjà donnée par le
    contexte de l'URL.
    """

    id: int
    eleve_id: int
    examen_id: int
    cours_id: int
    note: float
    statut: Optional[str]

from dataclasses import dataclass
from typing import Optional


@dataclass
class MaisonDTO:
    id: int
    nom: str
    couleur: str
    fondateur: str
    valeurs: Optional[str]
    reputation: int

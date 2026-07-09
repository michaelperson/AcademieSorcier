from dataclasses import dataclass
from typing import Optional


@dataclass
class EleveDTO:
    id: int
    nom: str
    annee_etude: int
    maison_id: int
    familier: Optional[str]
    statut: str

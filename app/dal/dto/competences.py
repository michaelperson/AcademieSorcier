from dataclasses import dataclass
from typing import Optional


@dataclass
class CompetenceDTO:
    id: int
    nom: str
    categorie: str
    description: str
    condition_type: str
    examen_id: Optional[int]
    note_min: Optional[float]

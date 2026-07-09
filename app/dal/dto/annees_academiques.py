from dataclasses import dataclass
from typing import Optional


@dataclass
class AnneeAcademiqueDTO:
    id: int
    libelle: str
    seuil_promotion: float
    cloturee_le: Optional[str]

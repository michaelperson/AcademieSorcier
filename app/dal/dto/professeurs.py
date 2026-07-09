from dataclasses import dataclass


@dataclass
class ProfesseurDTO:
    id: int
    nom: str
    matiere_enseignee: str
    anciennete: int

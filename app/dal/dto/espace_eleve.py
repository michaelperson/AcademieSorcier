from dataclasses import dataclass
from typing import Optional

from app.dal.dto.communs import EleveMinimalDTO


@dataclass
class MonCoursDTO:
    cours_id: int
    intitule: str
    statut_inscription: str
    date_inscription: str


@dataclass
class MaNoteDTO:
    examen_id: int
    titre_examen: str
    cours_id: int
    note: float
    statut: Optional[str]


@dataclass
class MonDossierDTO:
    id: int
    nom: str
    annee_etude: int
    maison: str
    familier: Optional[str]
    statut: str
    nombre_cours: int
    nombre_notes: int


@dataclass
class MaCompetenceDTO:
    competence_id: int
    nom: str
    categorie: str
    date_obtention: str
    source: str


@dataclass
class MonDuelDTO:
    duel_id: int
    tournoi_id: int
    tournoi_nom: str
    adversaire: EleveMinimalDTO
    issue: str

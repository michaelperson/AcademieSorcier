"""
DTOs de app/routes/examens.py : CRUD examen/résultat, plus les réponses
métier de clôture d'examen, clôture de cours (rapport et décision) et
évaluation de compétences — c'est le fichier de routes le plus dense du
projet, donc celui qui a le plus de DTOs.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ExamenDTO:
    id: int
    cours_id: int
    titre: str
    date: str
    seuil_reussite: float


@dataclass
class ResultatDTO:
    """Forme utilisée pour les résultats d'UN examen (cours_id ne serait
    qu'une redite de celui de l'examen déjà connu par l'appelant à cet
    endroit) — voir ResultatDetailleDTO (app/dal/dto/resultats.py) pour le
    listing global qui, lui, a besoin de préciser le cours.
    """

    id: int
    eleve_id: int
    examen_id: int
    note: float
    statut: Optional[str]


# --- Clôture d'un examen (cloturer_examen) -------------------------------


@dataclass
class ResultatClotureDTO:
    eleve_id: int
    note: float
    statut: str


@dataclass
class ClotureExamenDTO:
    examen_id: int
    seuil_reussite: float
    moyenne_examen: float
    resultats: List[ResultatClotureDTO]


# --- Évaluation de compétences (evaluer_competences) ---------------------


@dataclass
class MaitriseEntreeDTO:
    eleve_id: int
    competence: str


@dataclass
class EvaluerCompetencesDTO:
    examen_id: int
    competences_evaluees: List[str]
    maitrises_creees: List[MaitriseEntreeDTO]
    deja_debloquees: List[MaitriseEntreeDTO]


# --- Clôture d'un cours, mode rapport (_rapport_cloture_cours) -----------


@dataclass
class EleveRapportCoursDTO:
    eleve_id: int
    nom: str
    moyenne: Optional[float]
    statut: Optional[str]


@dataclass
class RapportClotureCoursDTO:
    cours_id: int
    intitule: str
    annee_academique: str
    eleves: List[EleveRapportCoursDTO]


# --- Clôture d'un cours, mode décision (_decider_cloture_cours) ----------


@dataclass
class CoursResumeDTO:
    id: int
    intitule: str
    annee_academique: str


@dataclass
class EleveResumeDTO:
    id: int
    nom: str
    maison: str


@dataclass
class ResultatExamenDTO:
    examen_id: int
    titre_examen: str
    note: float
    statut_examen: Optional[str]


@dataclass
class DecisionClotureCoursDTO:
    cours: CoursResumeDTO
    eleve: EleveResumeDTO
    resultats: List[ResultatExamenDTO]
    moyenne_cours: float
    seuil_retenu: float
    decision_finale: str
    nouveau_statut_inscription: str

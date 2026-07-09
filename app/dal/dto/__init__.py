"""
DTOs de sortie : la forme exacte de ce que chaque route renvoie en JSON,
sous forme de dataclasses plutôt que de dicts construits à la main.

Un fichier par domaine (maisons.py, cours.py, examens.py...), le même
découpage que app/routes/ — quand une route a plusieurs DTOs (examens.py
en a le plus, entre le CRUD et les trois endpoits de clôture), ils vivent
tous dans le fichier du même nom plutôt que d'être encore éclatés.

Ce module réexporte tout : une route fait `from app.dal.dto import
MaisonDTO, vers_dict` sans avoir à savoir dans quel fichier MaisonDTO vit
réellement, comme avant l'éclatement de l'ancien app/dto.py.

Ce que ces classes ne font pas, volontairement : elles ne valident rien.
La validation d'un payload entrant reste le rôle de marshmallow
(app/schemas.py, app/validation.py) — un DTO de sortie ne fait que décrire
une forme déjà connue et déjà correcte (elle sort de la base), il n'y a
rien à vérifier de ce côté-là.
"""

from app.dal.dto.communs import EleveMinimalDTO, vers_dict

from app.dal.dto.maisons import MaisonDTO
from app.dal.dto.professeurs import ProfesseurDTO
from app.dal.dto.cours import CoursDTO
from app.dal.dto.eleves import EleveDTO
from app.dal.dto.inscriptions import EleveDuCoursDTO, InscriptionDTO
from app.dal.dto.examens import (
    ClotureExamenDTO,
    CoursResumeDTO,
    DecisionClotureCoursDTO,
    EleveRapportCoursDTO,
    EleveResumeDTO,
    EvaluerCompetencesDTO,
    ExamenDTO,
    MaitriseEntreeDTO,
    RapportClotureCoursDTO,
    ResultatClotureDTO,
    ResultatDTO,
    ResultatExamenDTO,
)
from app.dal.dto.resultats import ResultatDetailleDTO
from app.dal.dto.competences import CompetenceDTO
from app.dal.dto.tournois import ClotureTournoiDTO, DuelDetailleDTO, DuelDTO, TournoiDTO
from app.dal.dto.annees_academiques import AnneeAcademiqueDTO
from app.dal.dto.espace_eleve import MaCompetenceDTO, MaNoteDTO, MonCoursDTO, MonDossierDTO, MonDuelDTO

__all__ = [
    "vers_dict",
    "EleveMinimalDTO",
    "MaisonDTO",
    "ProfesseurDTO",
    "CoursDTO",
    "EleveDTO",
    "InscriptionDTO",
    "EleveDuCoursDTO",
    "ExamenDTO",
    "ResultatDTO",
    "ResultatClotureDTO",
    "ClotureExamenDTO",
    "MaitriseEntreeDTO",
    "EvaluerCompetencesDTO",
    "EleveRapportCoursDTO",
    "RapportClotureCoursDTO",
    "CoursResumeDTO",
    "EleveResumeDTO",
    "ResultatExamenDTO",
    "DecisionClotureCoursDTO",
    "ResultatDetailleDTO",
    "CompetenceDTO",
    "TournoiDTO",
    "DuelDTO",
    "DuelDetailleDTO",
    "ClotureTournoiDTO",
    "AnneeAcademiqueDTO",
    "MonCoursDTO",
    "MaNoteDTO",
    "MonDossierDTO",
    "MaCompetenceDTO",
    "MonDuelDTO",
]

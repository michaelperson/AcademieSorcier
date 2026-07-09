"""
DTOs de sortie : la forme exacte de ce que chaque ressource renvoie en
JSON, sous forme de dataclasses plutôt que de dicts construits à la main.

Avant ce fichier, chaque route avait sa propre fonction `_serialize(...)`
qui assemblait un dict directement — ça fonctionnait, mais rien ne disait
qu'un `Eleve` renvoyait toujours les six mêmes champs dans le même ordre :
c'était une convention, pas un type. Une dataclass rend cette forme
explicite et vérifiable par un outil (mypy, l'autocomplétion de l'IDE),
un peu comme les DTOs Pydantic d'un autre projet du même genre.

Ce que ces classes ne font pas, volontairement : elles ne valident rien.
La validation d'un payload entrant reste le rôle de marshmallow
(app/schemas.py, app/validation.py) — un DTO de sortie ne fait que décrire
une forme déjà connue et déjà correcte (elle sort de la base), il n'y a
rien à vérifier de ce côté-là.

Chaque route continue de construire son dict pour jsonify() en appelant
`vers_dict(...)` sur l'instance de DTO — la forme JSON produite ne change
pas d'un octet par rapport à avant, seul le chemin pour y arriver gagne un
type intermédiaire.

Deuxième vague (ce fichier, suite) : les réponses des endpoints métier
(clôtures, évaluation de compétences, espace élève) sont elles aussi
typées maintenant, avec des DTOs imbriqués quand la réponse a plusieurs
niveaux (ex. ClotureExamenDTO contient une liste de ResultatClotureDTO).
`dataclasses.asdict()` descend récursivement dans ces imbrications tout
seul — un DTO qui contient un autre DTO se convertit correctement sans
code supplémentaire dans `vers_dict`.
"""

from dataclasses import asdict, dataclass
from typing import List, Optional


def vers_dict(dto) -> dict:
    """Convertit un DTO (n'importe laquelle des dataclasses ci-dessous) en
    dict prêt pour jsonify(). Un seul point de passage plutôt qu'un
    dataclasses.asdict() répété dans chaque route. Fonctionne aussi pour
    les DTOs imbriqués : asdict() est récursif.
    """
    return asdict(dto)


@dataclass
class MaisonDTO:
    id: int
    nom: str
    couleur: str
    fondateur: str
    valeurs: Optional[str]
    reputation: int


@dataclass
class ProfesseurDTO:
    id: int
    nom: str
    matiere_enseignee: str
    anciennete: int


@dataclass
class CoursDTO:
    id: int
    intitule: str
    niveau_requis: int
    capacite_max: int
    professeur_id: int
    annee_academique_id: int


@dataclass
class EleveDTO:
    id: int
    nom: str
    annee_etude: int
    maison_id: int
    familier: Optional[str]
    statut: str


@dataclass
class InscriptionDTO:
    id: int
    eleve_id: int
    cours_id: int
    date_inscription: str
    statut: str


@dataclass
class ExamenDTO:
    id: int
    cours_id: int
    titre: str
    date: str
    seuil_reussite: float


@dataclass
class ResultatDTO:
    """Forme utilisée par app/routes/examens.py (résultats d'UN examen —
    cours_id ne serait qu'une redite de celui de l'examen déjà connu par
    l'appelant à cet endroit).
    """

    id: int
    eleve_id: int
    examen_id: int
    note: float
    statut: Optional[str]


@dataclass
class ResultatDetailleDTO:
    """Forme utilisée par app/routes/resultats.py : le listing global des
    résultats (filtrable par cours ou examen) a besoin de préciser à quel
    cours chaque résultat appartient, contrairement à ResultatDTO ci-dessus
    où cette information est déjà donnée par le contexte de l'URL.
    """

    id: int
    eleve_id: int
    examen_id: int
    cours_id: int
    note: float
    statut: Optional[str]


@dataclass
class CompetenceDTO:
    id: int
    nom: str
    categorie: str
    description: str
    condition_type: str
    examen_id: Optional[int]
    note_min: Optional[float]


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
class AnneeAcademiqueDTO:
    id: int
    libelle: str
    seuil_promotion: float
    cloturee_le: Optional[str]


# --- Fragments réutilisés dans plusieurs DTOs composites ci-dessous ------


@dataclass
class EleveMinimalDTO:
    """Un élève réduit à (id, nom) : utilisé partout où une réponse a
    besoin de nommer un élève sans reprendre toute sa fiche (adversaire
    d'un duel, participant d'un duel, vainqueur d'un tournoi...).
    """

    id: int
    nom: str


# --- Clôture d'un examen (app/routes/examens.py::cloturer_examen) -------


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


# --- Évaluation de compétences (examens.py::evaluer_competences) --------


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


# --- Clôture d'un cours, mode rapport (examens.py::_rapport_cloture_cours)


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


# --- Clôture d'un cours, mode décision (examens.py::_decider_cloture_cours)


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


# --- Tournois et duels (app/routes/tournois.py) --------------------------


@dataclass
class DuelDetailleDTO:
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


# --- Élèves d'un cours (app/routes/inscriptions.py) ----------------------


@dataclass
class EleveDuCoursDTO:
    eleve_id: int
    nom: str
    maison: str
    statut_inscription: str


# --- Espace élève (app/routes/espace_eleve.py) ---------------------------


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

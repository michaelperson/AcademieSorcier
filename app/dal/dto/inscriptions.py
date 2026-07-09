from dataclasses import dataclass


@dataclass
class InscriptionDTO:
    id: int
    eleve_id: int
    cours_id: int
    date_inscription: str
    statut: str


@dataclass
class EleveDuCoursDTO:
    """Utilisée par GET /cours/<id>/eleves (app/routes/inscriptions.py) :
    une projection à cheval sur Eleve et Maison, pas la forme d'une seule
    entité isolée.
    """

    eleve_id: int
    nom: str
    maison: str
    statut_inscription: str

from dataclasses import dataclass


@dataclass
class CoursDTO:
    id: int
    intitule: str
    niveau_requis: int
    capacite_max: int
    professeur_id: int
    annee_academique_id: int

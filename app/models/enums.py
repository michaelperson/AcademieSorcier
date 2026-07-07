from enum import Enum


class StatutEleve(str, Enum):
    ACTIF = "actif"
    DIPLOME = "diplome"
    RENVOYE = "renvoye"


class RoleUtilisateur(str, Enum):
    ELEVE = "eleve"
    PROFESSEUR = "professeur"
    ADMIN = "admin"


class StatutInscription(str, Enum):
    INSCRIT = "inscrit"
    EN_COURS = "en_cours"
    VALIDE = "valide"
    ABANDONNE = "abandonne"


class SourceDeblocage(str, Enum):
    """Origine d'une condition de déblocage (Competence.condition_type) ou
    d'un déblocage effectif (Maitrise.source) : un examen ou un tournoi.
    Les deux entités partagent ce vocabulaire, d'où l'enum commun.
    """

    EXAMEN = "examen"
    TOURNOI = "tournoi"

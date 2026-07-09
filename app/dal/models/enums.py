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


class StatutResultat(str, Enum):
    """Réussite/échec à UN examen précis. À ne pas confondre avec
    StatutInscription, qui reflète la situation de l'élève sur l'ensemble
    du cours (voir Inscription.statut) : un élève peut très bien échouer
    un examen et rester "en_cours" dans le cours si sa moyenne générale
    tient la route. Fixé par la clôture de l'examen (POST
    /examens/<id>/cloture) ; vaut None tant que l'examen n'est pas clôturé.
    """

    REUSSI = "reussi"
    ECHEC = "echec"


class SourceDeblocage(str, Enum):
    """Origine d'une condition de déblocage (Competence.condition_type) ou
    d'un déblocage effectif (Maitrise.source) : un examen ou un tournoi.
    Les deux entités partagent ce vocabulaire, d'où l'enum commun.
    """

    EXAMEN = "examen"
    TOURNOI = "tournoi"
